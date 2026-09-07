package com.casait.emtgateway.domain.model

enum class MonitorConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    MONITORING,
    MONITOR_DATA_LOST
}

enum class TransportType {
    USB,
    ETHERNET
}

enum class InternetState {
    ONLINE,
    OFFLINE
}

enum class SyncState {
    IDLE,
    SYNCING,
    PAUSED_OFFLINE
}

enum class CaseStatus {
    NO_ACTIVE_CASE,
    CREATING_CASE,
    MONITORING_ACTIVE,
    CASE_CLOSED
}

data class GatewayState(
    val caseStatus: CaseStatus = CaseStatus.NO_ACTIVE_CASE,
    val activeCaseId: String = "NONE",
    val activePatientName: String = "",
    val activeAge: Int = 0,
    val activeSex: String = "Male",
    val activeClassification: String = "Adult", // Adult, Pediatric, Neonate
    val activeEsiLevel: Int = 3, // ESI Level 1 to 5
    val activeEsiReason: String = "Vitals within normal physiological limits",
    val activeEsiGeneration: String = "AUTOMATIC",
    val monitorState: MonitorConnectionState = MonitorConnectionState.DISCONNECTED,
    val transportType: TransportType = TransportType.ETHERNET,
    val internetState: InternetState = InternetState.OFFLINE,
    val syncState: SyncState = SyncState.IDLE,
    val monitorIp: String = "127.0.0.1",
    val monitorPort: Int = 8000,
    val activeSessionId: String = "NONE",
    val sourceIdentifier: String = "VIRTUAL_CMS8000",
    val unsyncedRecordCount: Int = 0,
    val lastSyncTimestamp: String = "NEVER",
    val currentLatencyMs: Long = 0L
)
