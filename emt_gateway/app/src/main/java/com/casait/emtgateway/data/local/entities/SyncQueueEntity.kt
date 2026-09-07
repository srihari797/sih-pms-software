package com.casait.emtgateway.data.local.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "sync_queue",
    indices = [
        Index(value = ["status"]),
        Index(value = ["createdAt"])
    ]
)
data class SyncQueueEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val dataType: String,
    val recordId: String,
    val payloadJson: String,
    val createdAt: String,
    val retryCount: Int = 0,
    val status: String = "PENDING", // PENDING, SENDING, SYNCED, FAILED
    val lastAttempt: String? = null,
    val lastError: String? = null
)
