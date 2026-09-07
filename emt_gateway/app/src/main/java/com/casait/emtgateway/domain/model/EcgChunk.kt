package com.casait.emtgateway.domain.model

data class EcgChunk(
    val patientId: String,
    val sessionId: String,
    val lead: String = "II",
    val sampleRate: Int = 250,
    val sourceTimestamp: String,
    val receivedTimestamp: String,
    val samples: List<Double>
)
