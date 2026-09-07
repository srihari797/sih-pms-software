package com.casait.emtgateway.domain.model

data class BpData(
    val sys: Int?,
    val dia: Int?,
    val map: Int?,
    val status: String? = "IDLE"
)

data class TempData(
    val t1: Double?,
    val t2: Double?
)

data class VitalReading(
    val patientId: String,
    val sessionId: String,
    val sourceTimestamp: String,
    val receivedTimestamp: String,
    val latencyMs: Long,
    val source: String = "SIMULATOR",
    val hr: Int?,
    val spo2: Int?,
    val pr: Int?,
    val bp: BpData?,
    val rr: Int?,
    val temp: TempData?,
    val sensors: Map<String, Boolean> = emptyMap()
)
