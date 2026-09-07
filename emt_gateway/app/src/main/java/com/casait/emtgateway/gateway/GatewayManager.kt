package com.casait.emtgateway.gateway

import android.content.Context
import android.util.Log
import com.casait.emtgateway.data.local.AppDatabase
import com.casait.emtgateway.data.local.entities.EcgEntity
import com.casait.emtgateway.data.local.entities.PatientEntity
import com.casait.emtgateway.data.local.entities.SessionEntity
import com.casait.emtgateway.data.local.entities.SyncQueueEntity
import com.casait.emtgateway.data.local.entities.TriageAssessmentEntity
import com.casait.emtgateway.data.local.entities.VitalEntity
import com.casait.emtgateway.domain.model.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.time.Instant
import java.util.UUID

class GatewayManager(private val context: Context) {
    private val TAG = "GatewayManager"
    private val scope = CoroutineScope(Dispatchers.IO)
    private val db = AppDatabase.getDatabase(context)

    val connectionManager = ConnectionManager(context)
    val syncManager = SyncManager(db.syncQueueDao())
    val validationEngine = ValidationEngine()

    private val _gatewayState = MutableStateFlow(GatewayState())
    val gatewayState: StateFlow<GatewayState> = _gatewayState.asStateFlow()

    private val _latestVital = MutableStateFlow<VitalReading?>(null)
    val latestVital: StateFlow<VitalReading?> = _latestVital.asStateFlow()

    private var lastPacketReceivedAt: Long = 0L

    init {
        Log.i(TAG, "GATEWAY_MANAGER_INITIALIZED: Starting state observation and heartbeat loops.")
        observeStateChanges()
        startHeartbeatMonitor()
    }

    private fun observeStateChanges() {
        scope.launch {
            combine(
                connectionManager.connectionState,
                connectionManager.transportType,
                syncManager.internetState,
                syncManager.syncState,
                db.syncQueueDao().getUnsyncedCountFlow()
            ) { connState, transport, netState, syncState, unsyncedCount ->
                _gatewayState.value.copy(
                    monitorState = connState,
                    transportType = transport,
                    internetState = netState,
                    syncState = syncState,
                    unsyncedRecordCount = unsyncedCount,
                    lastSyncTimestamp = syncManager.lastSyncTime.value
                )
            }.collect { updatedState ->
                _gatewayState.value = updatedState
            }
        }
    }

    private fun startHeartbeatMonitor() {
        scope.launch {
            while (true) {
                kotlinx.coroutines.delay(1000)
                if (lastPacketReceivedAt > 0L && System.currentTimeMillis() - lastPacketReceivedAt > 4000L) {
                    val currentState = connectionManager.connectionState.value
                    if (currentState == MonitorConnectionState.MONITORING || currentState == MonitorConnectionState.CONNECTED) {
                        Log.w(TAG, "HEARTBEAT_TIMEOUT: No vital packets received for > 4s. Setting MONITOR_DATA_LOST.")
                        connectionManager.setConnectedState(MonitorConnectionState.MONITOR_DATA_LOST)
                        _latestVital.value = null
                        connectionManager.disconnect()
                    }
                }
            }
        }
    }

    fun prepareNewCase() {
        _gatewayState.value = _gatewayState.value.copy(
            caseStatus = CaseStatus.CREATING_CASE
        )
    }

    fun createAndStartCase(name: String, age: Int, sex: String, classification: String, esiLevel: Int = 3) {
        val newCaseId = "CASE-${System.currentTimeMillis()}"
        val patientName = if (name.isNotBlank()) name else "Raj Kumar"
        lastPacketReceivedAt = System.currentTimeMillis()
        Log.i(TAG, "START_CASE: Created new patient case $newCaseId for $patientName")
        _gatewayState.value = _gatewayState.value.copy(
            caseStatus = CaseStatus.MONITORING_ACTIVE,
            activeCaseId = newCaseId,
            activePatientName = patientName,
            activeAge = age,
            activeSex = sex,
            activeClassification = classification,
            activeEsiLevel = esiLevel
        )

        // Persist PatientEntity to Room
        scope.launch {
            val patient = PatientEntity(
                patientId = newCaseId,
                name = patientName,
                age = age,
                sex = sex,
                classification = classification,
                createdAt = Instant.now().toString()
            )
            db.patientDao().insertPatient(patient)
        }

        // Query UsbManager.deviceList and dynamic gateway IPs IMMEDIATELY on case start
        scope.launch {
            Log.i(TAG, "START_CASE: Querying UsbConnectionManager for existing connected hardware...")
            connectionManager.connect()
        }
    }

    fun closeCurrentCase() {
        Log.i(TAG, "CLOSE_CASE: Closing case ${_gatewayState.value.activeCaseId}. USB hardware manager remains running.")
        _gatewayState.value = _gatewayState.value.copy(
            caseStatus = CaseStatus.NO_ACTIVE_CASE,
            activeCaseId = "NONE",
            activePatientName = "",
            activeAge = 0
        )
        _latestVital.value = null
        lastPacketReceivedAt = 0L
    }

    suspend fun connect(transport: TransportType = TransportType.ETHERNET, ip: String = "127.0.0.1", port: Int = 8000): Boolean {
        connectionManager.setTransportType(transport, ip, port)
        listenToIncomingStream()
        return connectionManager.connect()
    }

    suspend fun disconnect() {
        connectionManager.disconnect()
        _latestVital.value = null
        lastPacketReceivedAt = 0L
    }

    fun onUsbDeviceAttached(device: android.hardware.usb.UsbDevice? = null) {
        Log.i(TAG, "ON_USB_DEVICE_ATTACHED: Triggering connection attempt.")
        scope.launch {
            connectionManager.usbConnectionManager.onUsbDeviceAttached(device)
            enqueueConnectionStatusEvent("CONNECTED")
        }
    }

    fun onUsbDeviceDetached(device: android.hardware.usb.UsbDevice? = null) {
        Log.i(TAG, "ON_USB_DEVICE_DETACHED: Clearing vitals and setting DISCONNECTED state.")
        scope.launch {
            _latestVital.value = null
            enqueueConnectionStatusEvent("DISCONNECTED")
            connectionManager.usbConnectionManager.onUsbDeviceDetached(device)
        }
    }

    private fun listenToIncomingStream() {
        scope.launch {
            connectionManager.observeIncomingData()
                .collect { jsonString ->
                    processIncomingPayload(jsonString)
                }
        }
    }

    private suspend fun processIncomingPayload(jsonString: String) {
        lastPacketReceivedAt = System.currentTimeMillis()
        connectionManager.setConnectedState(MonitorConnectionState.MONITORING)
        val nowIso = Instant.now().toString()
        try {
            val json = JSONObject(jsonString)
            val eventType = json.optString("event", json.optString("type"))

            val isVitalEvent = eventType == "VITAL_UPDATE" || eventType == "PATIENT_MONITOR_UPDATE" ||
                               json.has("data") || json.has("hr") || json.has("heart_rate")

            if (isVitalEvent) {
                val caseId = _gatewayState.value.activeCaseId
                val sessionId = json.optString("session_id", "SESSION_001")
                val sourceTime = json.optString("timestamp", nowIso)
                val source = json.optString("source", "VIRTUAL_CMS8000")

                var hr: Int? = null
                var spo2: Int? = null
                var pr: Int? = null
                var sys: Int? = null
                var dia: Int? = null
                var mapVal: Int? = null
                var bpStatus: String? = "IDLE"
                var rr: Int? = null
                var t1: Double? = null
                var t2: Double? = null

                if (json.has("data") && !json.isNull("data")) {
                    val d = json.getJSONObject("data")
                    if (d.has("heart_rate") && !d.isNull("heart_rate")) {
                        val hrObj = d.getJSONObject("heart_rate")
                        if (hrObj.has("value") && !hrObj.isNull("value")) hr = hrObj.getInt("value")
                    }
                    if (d.has("spo2") && !d.isNull("spo2")) {
                        val sObj = d.getJSONObject("spo2")
                        if (sObj.has("value") && !sObj.isNull("value")) spo2 = sObj.getInt("value")
                    }
                    if (d.has("pulse_rate") && !d.isNull("pulse_rate")) {
                        val prObj = d.getJSONObject("pulse_rate")
                        if (prObj.has("value") && !prObj.isNull("value")) pr = prObj.getInt("value")
                    }
                    if (d.has("blood_pressure") && !d.isNull("blood_pressure")) {
                        val bpObj = d.getJSONObject("blood_pressure")
                        if (bpObj.has("systolic") && !bpObj.isNull("systolic")) sys = bpObj.getInt("systolic")
                        if (bpObj.has("diastolic") && !bpObj.isNull("diastolic")) dia = bpObj.getInt("diastolic")
                        if (bpObj.has("map") && !bpObj.isNull("map")) mapVal = bpObj.getInt("map")
                    }
                    if (d.has("respiratory_rate") && !d.isNull("respiratory_rate")) {
                        val rrObj = d.getJSONObject("respiratory_rate")
                        if (rrObj.has("value") && !rrObj.isNull("value")) rr = rrObj.getInt("value")
                    }
                    if (d.has("temperature") && !d.isNull("temperature")) {
                        val tempObj = d.getJSONObject("temperature")
                        if (tempObj.has("t1") && !tempObj.isNull("t1")) {
                            val t1Obj = tempObj.getJSONObject("t1")
                            if (t1Obj.has("value") && !t1Obj.isNull("value")) t1 = t1Obj.getDouble("value")
                        }
                        if (tempObj.has("t2") && !tempObj.isNull("t2")) {
                            val t2Obj = tempObj.getJSONObject("t2")
                            if (t2Obj.has("value") && !t2Obj.isNull("value")) t2 = t2Obj.getDouble("value")
                        }
                    }
                } else {
                    // Legacy dict fallback
                    if (json.has("hr") && !json.isNull("hr")) hr = json.optInt("hr")
                    if (json.has("spo2") && !json.isNull("spo2")) spo2 = json.optInt("spo2")
                    if (json.has("pr") && !json.isNull("pr")) pr = json.optInt("pr")
                    if (json.has("rr") && !json.isNull("rr")) rr = json.optInt("rr")
                    if (json.has("bp") && !json.isNull("bp")) {
                        val bpObj = json.getJSONObject("bp")
                        if (bpObj.has("sys") && !bpObj.isNull("sys")) sys = bpObj.optInt("sys")
                        if (bpObj.has("dia") && !bpObj.isNull("dia")) dia = bpObj.optInt("dia")
                        if (bpObj.has("map") && !bpObj.isNull("map")) mapVal = bpObj.optInt("map")
                    }
                    if (json.has("temp") && !json.isNull("temp")) {
                        val tempObj = json.getJSONObject("temp")
                        if (tempObj.has("t1") && !tempObj.isNull("t1")) t1 = tempObj.optDouble("t1")
                        if (tempObj.has("t2") && !tempObj.isNull("t2")) t2 = tempObj.optDouble("t2")
                    }
                }

                val latency = validationEngine.calculateLatencyMs(sourceTime, nowIso)

                val reading = VitalReading(
                    patientId = caseId,
                    sessionId = sessionId,
                    sourceTimestamp = sourceTime,
                    receivedTimestamp = nowIso,
                    latencyMs = latency,
                    source = source,
                    hr = hr,
                    spo2 = spo2,
                    pr = pr,
                    bp = BpData(sys, dia, mapVal, bpStatus),
                    rr = rr,
                    temp = TempData(t1, t2)
                )

                if (validationEngine.validateVitalReading(reading)) {
                    Log.i(TAG, "VITAL_UPDATE received: HR=$hr SpO2=$spo2 BP=$sys/$dia RR=$rr TEMP=$t1")
                    _latestVital.value = reading
                    val esiResult = com.casait.emtgateway.domain.model.EsiTriageEngine.evaluate(reading)
                    _gatewayState.value = _gatewayState.value.copy(
                        activeSessionId = sessionId,
                        sourceIdentifier = source,
                        currentLatencyMs = latency,
                        activeEsiLevel = esiResult.level,
                        activeEsiReason = esiResult.reason,
                        activeEsiGeneration = esiResult.generation
                    )

                    // Persist to Room database & offline sync queue when monitoring case is active
                    if (_gatewayState.value.caseStatus == CaseStatus.MONITORING_ACTIVE) {
                        val vitalEventId = "EVT_${UUID.randomUUID().toString().take(12).uppercase()}"
                        val assessmentId = "TRI_${UUID.randomUUID().toString().take(10).uppercase()}"

                        // Ensure Patient & Session foreign key parents exist
                        db.patientDao().insertPatient(
                            PatientEntity(
                                patientId = caseId,
                                name = _gatewayState.value.activePatientName.ifBlank { "Raj Kumar" },
                                age = _gatewayState.value.activeAge,
                                sex = _gatewayState.value.activeSex,
                                classification = _gatewayState.value.activeClassification,
                                createdAt = nowIso
                            )
                        )
                        db.sessionDao().insertSession(
                            SessionEntity(
                                sessionId = sessionId,
                                patientId = caseId,
                                startedAt = nowIso,
                                status = "ACTIVE",
                                ambulanceId = "AMB-01",
                                finalEsiLevel = esiResult.level
                            )
                        )

                        // 1. Insert VitalEntity with unique eventId
                        val vitalRowId = db.vitalDao().insertVital(
                            VitalEntity(
                                eventId = vitalEventId,
                                sessionId = sessionId,
                                patientId = caseId,
                                sourceTimestamp = sourceTime,
                                receivedTimestamp = nowIso,
                                latencyMs = latency,
                                source = source,
                                hr = hr,
                                spo2 = spo2,
                                pr = pr,
                                sys = sys,
                                dia = dia,
                                map = mapVal,
                                rr = rr,
                                temp1 = t1,
                                temp2 = t2
                            )
                        )

                        // 2. Insert TriageAssessmentEntity
                        db.triageAssessmentDao().insertAssessment(
                            TriageAssessmentEntity(
                                assessmentId = assessmentId,
                                sessionId = sessionId,
                                patientId = caseId,
                                vitalReadingId = vitalRowId,
                                esiLevel = esiResult.level,
                                generationMethod = "AUTOMATIC",
                                reason = esiResult.reason,
                                assessedAt = nowIso
                            )
                        )

                        // 3. Enqueue PATIENT_MONITOR_UPDATE with recordId = vitalEventId (Idempotent!)
                        val phase3Payload = buildPhase3PayloadJson(caseId, sessionId, sourceTime, hr, spo2, pr, sys, dia, mapVal, rr, t1, t2, vitalEventId)
                        db.syncQueueDao().enqueue(
                            SyncQueueEntity(
                                dataType = "PATIENT_MONITOR_UPDATE",
                                recordId = vitalEventId,
                                payloadJson = phase3Payload,
                                createdAt = nowIso
                            )
                        )

                        // 4. Enqueue derived PATIENT_TRIAGE_UPDATE
                        val triagePayload = buildTriagePayloadJson(caseId, sessionId, nowIso, hr, spo2, sys, dia, mapVal, rr, esiResult, assessmentId)
                        db.syncQueueDao().enqueue(
                            SyncQueueEntity(
                                dataType = "PATIENT_TRIAGE_UPDATE",
                                recordId = assessmentId,
                                payloadJson = triagePayload,
                                createdAt = nowIso
                            )
                        )
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Payload parse error", e)
        }
    }

    private fun enqueueConnectionStatusEvent(deviceStatus: String) {
        if (_gatewayState.value.caseStatus != CaseStatus.MONITORING_ACTIVE) return
        val nowIso = Instant.now().toString()
        val eventObj = JSONObject().apply {
            put("event", "MONITOR_CONNECTION_STATUS")
            put("event_id", "EVT_${UUID.randomUUID().toString().take(8).uppercase()}")
            put("case_id", _gatewayState.value.activeCaseId)
            put("monitor_session_id", _gatewayState.value.activeSessionId)
            put("timestamp", nowIso)
            put("monitor", JSONObject().apply {
                put("source", "VIRTUAL_CMS8000")
                put("connection", _gatewayState.value.transportType.name)
                put("device_status", deviceStatus)
            })
        }

        scope.launch {
            db.syncQueueDao().enqueue(
                SyncQueueEntity(
                    dataType = "MONITOR_CONNECTION_STATUS",
                    recordId = System.currentTimeMillis().toString(),
                    payloadJson = eventObj.toString(),
                    createdAt = nowIso
                )
            )
        }
    }

    private fun buildTriagePayloadJson(
        caseId: String,
        sessionId: String,
        timestamp: String,
        hr: Int?, spo2: Int?, sys: Int?, dia: Int?, mapVal: Int?, rr: Int?,
        esiResult: com.casait.emtgateway.domain.model.EsiResult,
        assessmentId: String = ""
    ): String {
        val root = JSONObject()
        root.put("event", "PATIENT_TRIAGE_UPDATE")
        root.put("assessment_id", if (assessmentId.isNotBlank()) assessmentId else "TRI_${UUID.randomUUID().toString().take(10).uppercase()}")
        root.put("session_id", sessionId)
        root.put("patient_id", caseId)
        root.put("timestamp", timestamp)
        root.put("patient", JSONObject().apply {
            put("name", _gatewayState.value.activePatientName)
        })
        root.put("source", "ANDROID_EMT_GATEWAY")

        val triageObj = JSONObject().apply {
            put("esi_level", esiResult.level)
            put("generation", esiResult.generation)
            put("reason", esiResult.reason)
        }
        root.put("triage", triageObj)

        val vitalsObj = JSONObject().apply {
            put("heart_rate", JSONObject().apply { put("value", hr ?: JSONObject.NULL); put("unit", "bpm") })
            put("spo2", JSONObject().apply { put("value", spo2 ?: JSONObject.NULL); put("unit", "%") })
            put("blood_pressure", JSONObject().apply {
                put("systolic", sys ?: JSONObject.NULL)
                put("diastolic", dia ?: JSONObject.NULL)
                put("map", mapVal ?: JSONObject.NULL)
                put("unit", "mmHg")
            })
            put("respiratory_rate", JSONObject().apply { put("value", rr ?: JSONObject.NULL); put("unit", "breaths/min") })
        }
        root.put("vitals", vitalsObj)

        return root.toString()
    }

    private fun buildPhase3PayloadJson(
        caseId: String,
        sessionId: String,
        timestamp: String,
        hr: Int?, spo2: Int?, pr: Int?, sys: Int?, dia: Int?, mapVal: Int?, rr: Int?, t1: Double?, t2: Double?,
        eventId: String = ""
    ): String {
        val root = JSONObject()
        root.put("event", "PATIENT_MONITOR_UPDATE")
        root.put("event_id", if (eventId.isNotBlank()) eventId else "EVT_${UUID.randomUUID().toString().take(12).uppercase()}")
        root.put("timestamp", timestamp)

        val caseObj = JSONObject().apply {
            put("case_id", caseId)
            put("patient_name", _gatewayState.value.activePatientName)
            put("age", _gatewayState.value.activeAge)
            put("sex", _gatewayState.value.activeSex.uppercase())
            put("classification", _gatewayState.value.activeClassification.uppercase())
            put("esi_level", _gatewayState.value.activeEsiLevel)
        }
        root.put("case", caseObj)

        val monitorObj = JSONObject().apply {
            put("source", "VIRTUAL_CMS8000")
            put("monitor_session_id", sessionId)
            put("connection", _gatewayState.value.transportType.name)
            put("device_status", _gatewayState.value.monitorState.name)
        }
        root.put("monitor", monitorObj)

        val dataObj = JSONObject().apply {
            put("heart_rate", JSONObject().apply { put("value", hr ?: JSONObject.NULL); put("unit", "bpm") })
            put("spo2", JSONObject().apply { put("value", spo2 ?: JSONObject.NULL); put("unit", "%") })
            put("pulse_rate", JSONObject().apply { put("value", pr ?: JSONObject.NULL); put("unit", "bpm") })
            put("blood_pressure", JSONObject().apply {
                put("systolic", sys ?: JSONObject.NULL)
                put("diastolic", dia ?: JSONObject.NULL)
                put("map", mapVal ?: JSONObject.NULL)
                put("unit", "mmHg")
            })
            put("respiratory_rate", JSONObject().apply { put("value", rr ?: JSONObject.NULL); put("unit", "breaths/min") })
            put("temperature", JSONObject().apply {
                put("t1", JSONObject().apply { put("value", t1 ?: JSONObject.NULL); put("unit", "°C") })
                put("t2", JSONObject().apply { put("value", t2 ?: JSONObject.NULL); put("unit", "°C") })
            })
        }
        root.put("data", dataObj)

        val triageObj = JSONObject().apply {
            put("esi_level", _gatewayState.value.activeEsiLevel)
            put("generation", _gatewayState.value.activeEsiGeneration)
            put("reason", _gatewayState.value.activeEsiReason)
        }
        root.put("triage", triageObj)

        return root.toString()
    }
}
