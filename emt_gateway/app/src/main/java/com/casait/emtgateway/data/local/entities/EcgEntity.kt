package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "ecg_samples",
    indices = [
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
data class EcgEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val chunkId: String = "",
    val sessionId: String,
    val patientId: String,
    val lead: String,
    val sampleRate: Int,
    val sourceTimestamp: String,
    val receivedTimestamp: String,
    val samplesJson: String
)
