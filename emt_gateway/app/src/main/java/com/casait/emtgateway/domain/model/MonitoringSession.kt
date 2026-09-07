package com.casait.emtgateway.domain.model

data class MonitoringSession(
    val sessionId: String,
    val patientId: String,
    val startedAt: String,
    val endedAt: String? = null,
    val status: String = "ACTIVE"
)
