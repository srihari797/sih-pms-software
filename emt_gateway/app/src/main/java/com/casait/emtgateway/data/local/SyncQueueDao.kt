package com.casait.emtgateway.data.local

import androidx.room.*
import com.casait.emtgateway.data.local.entities.SyncQueueEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SyncQueueDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun enqueue(item: SyncQueueEntity): Long

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status != 'SYNCED'")
    fun getUnsyncedCountFlow(): Flow<Int>

    @Query("SELECT COUNT(*) FROM sync_queue WHERE status != 'SYNCED'")
    suspend fun getUnsyncedCount(): Int

    @Query("SELECT * FROM sync_queue WHERE status = 'PENDING' ORDER BY id ASC LIMIT :limit")
    suspend fun getPendingItems(limit: Int = 20): List<SyncQueueEntity>

    @Query("UPDATE sync_queue SET status = :status, lastAttempt = :timestamp, lastError = :lastError, retryCount = retryCount + 1 WHERE id = :id")
    suspend fun updateStatus(id: Long, status: String, timestamp: String, lastError: String? = null)

    @Query("DELETE FROM sync_queue WHERE status = 'SYNCED'")
    suspend fun purgeSynced()
}
