package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "monitoring_sessions",
    indices = [Index(value = ["patientId"])],
    foreignKeys = [
        ForeignKey(
            entity = PatientEntity::class,
            parentColumns = ["patientId"],
            childColumns = ["patientId"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class SessionEntity(
    @PrimaryKey val sessionId: String,
    val patientId: String,
    val startedAt: String,
    val endedAt: String? = null,
    val status: String = "ACTIVE",
    val ambulanceId: String = "AMB-01",
    val finalEsiLevel: Int? = null
)
