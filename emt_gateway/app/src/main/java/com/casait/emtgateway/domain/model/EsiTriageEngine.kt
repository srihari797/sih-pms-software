package com.casait.emtgateway.domain.model

data class EsiResult(
    val level: Int,
    val categoryName: String,
    val reason: String,
    val generation: String = "AUTOMATIC"
)

object EsiTriageEngine {
    fun evaluate(vital: VitalReading?): EsiResult {
        if (vital == null) {
            return EsiResult(
                level = 3,
                categoryName = "URGENT (ESI 3)",
                reason = "Awaiting live vital stream for automatic triage assessment",
                generation = "AUTOMATIC"
            )
        }

        val hr = vital.hr
        val spo2 = vital.spo2
        val sys = vital.bp?.sys
        val rr = vital.rr

        val reasons = mutableListOf<String>()

        // 1. Check ESI Level 1 (Critical / Resuscitation / Immediate)
        var isEsi1 = false
        if (spo2 != null && spo2 < 85) {
            isEsi1 = true
            reasons.add("Critical SpO2 ($spo2%)")
        }
        if (hr != null && (hr < 40 || hr > 150)) {
            isEsi1 = true
            reasons.add("Extreme HR ($hr bpm)")
        }
        if (rr != null && (rr < 8 || rr > 35)) {
            isEsi1 = true
            reasons.add("Extreme RR ($rr/min)")
        }
        if (sys != null && sys < 80) {
            isEsi1 = true
            reasons.add("Severe hypotension (SYS $sys mmHg)")
        }

        if (isEsi1) {
            return EsiResult(
                level = 1,
                categoryName = "IMMEDIATE (ESI 1)",
                reason = reasons.joinToString(" + "),
                generation = "AUTOMATIC"
            )
        }

        // 2. Check ESI Level 2 (Emergent / High Risk)
        var isEsi2 = false
        if (spo2 != null && spo2 < 92) {
            isEsi2 = true
            reasons.add("Low SpO2 ($spo2%)")
        }
        if (hr != null && hr > 120) {
            isEsi2 = true
            reasons.add("Tachycardia ($hr bpm)")
        }
        if (rr != null && rr > 28) {
            isEsi2 = true
            reasons.add("Tachypnea ($rr/min)")
        }
        if (sys != null && sys < 90) {
            isEsi2 = true
            reasons.add("Hypotension (SYS $sys mmHg)")
        }

        if (isEsi2) {
            return EsiResult(
                level = 2,
                categoryName = "EMERGENT (ESI 2)",
                reason = if (reasons.size >= 2) "Low SpO2 with hypotension and elevated respiratory rate" else reasons.joinToString(" + "),
                generation = "AUTOMATIC"
            )
        }

        // 3. Check ESI Level 3 (Urgent / Moderate Risk)
        var isEsi3 = false
        if (spo2 != null && spo2 < 95) {
            isEsi3 = true
            reasons.add("Mild hypoxia ($spo2%)")
        }
        if (hr != null && hr > 100) {
            isEsi3 = true
            reasons.add("Elevated HR ($hr bpm)")
        }
        if (rr != null && rr > 20) {
            isEsi3 = true
            reasons.add("Elevated RR ($rr/min)")
        }
        if (sys != null && (sys < 100 || sys > 160)) {
            isEsi3 = true
            reasons.add("Borderline BP (SYS $sys mmHg)")
        }

        if (isEsi3) {
            return EsiResult(
                level = 3,
                categoryName = "URGENT (ESI 3)",
                reason = reasons.joinToString(" + "),
                generation = "AUTOMATIC"
            )
        }

        // 4. Default: ESI Level 4 / 5 (Less Urgent / Non-Urgent)
        return EsiResult(
            level = 4,
            categoryName = "LESS URGENT (ESI 4)",
            reason = "Vitals within normal physiological limits",
            generation = "AUTOMATIC"
        )
    }
}
