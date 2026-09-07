package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "triage_assessments",
    indices = [
        Index(value = ["sessionId"]),
        Index(value = ["patientId"]),
        Index(value = ["vitalReadingId"])
    ],
    foreignKeys = [
        ForeignKey(
            entity = SessionEntity::class,
            parentColumns = ["sessionId"],
            childColumns = ["sessionId"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class TriageAssessmentEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val assessmentId: String,
    val sessionId: String,
    val patientId: String,
    val vitalReadingId: Long,
    val esiLevel: Int,
    val generationMethod: String = "AUTOMATIC",
    val reason: String,
    val assessedAt: String
)
