package com.casait.emtgateway.gateway

import com.casait.emtgateway.domain.model.VitalReading
import java.time.Instant

class ValidationEngine {

    fun validateVitalReading(reading: VitalReading): Boolean {
        // HR check: 20-250 bpm (allow null for disconnected sensors)
        reading.hr?.let {
            if (it !in 20..250) return false
        }
        // SpO2 check: 0-100 %
        reading.spo2?.let {
            if (it !in 0..100) return false
        }
        // RR check: 0-100 /min
        reading.rr?.let {
            if (it !in 0..100) return false
        }
        // Temp check: 25.0 - 45.0 °C
        reading.temp?.t1?.let {
            if (it !in 25.0..45.0) return false
        }
        // BP check: SYS > DIA if both present
        reading.bp?.let { bp ->
            if (bp.sys != null && bp.dia != null) {
                if (bp.sys <= bp.dia) return false
            }
        }

        return true
    }

    fun calculateLatencyMs(sourceTimestamp: String, receivedTimestamp: String): Long {
        return try {
            val sourceTime = Instant.parse(sourceTimestamp).toEpochMilli()
            val receivedTime = Instant.parse(receivedTimestamp).toEpochMilli()
            maxOf(0L, receivedTime - sourceTime)
        } catch (e: Exception) {
            0L
        }
    }
}
