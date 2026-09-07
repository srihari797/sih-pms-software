package com.casait.emtgateway.domain.model

data class SensorStatus(
    val ecg: Boolean = true,
    val spo2: Boolean = true,
    val nibp: Boolean = true,
    val temp1: Boolean = true,
    val temp2: Boolean = true,
    val updatedAt: String
)
