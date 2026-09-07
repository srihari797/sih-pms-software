package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "vital_readings",
    indices = [
        Index(value = ["eventId"], unique = true),
        Index(value = ["sessionId"]),
        Index(value = ["patientId"])
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
data class VitalEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventId: String,
    val sessionId: String,
    val patientId: String,
    val sourceTimestamp: String,
    val receivedTimestamp: String,
    val latencyMs: Long,
    val source: String,
    val hr: Int?,
    val spo2: Int?,
    val pr: Int?,
    val sys: Int?,
    val dia: Int?,
    val map: Int?,
    val rr: Int?,
    val temp1: Double?,
    val temp2: Double?
)
