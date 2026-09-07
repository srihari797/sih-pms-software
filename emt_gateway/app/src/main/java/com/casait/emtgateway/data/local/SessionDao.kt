package com.casait.emtgateway.data.local

import androidx.room.*
import com.casait.emtgateway.data.local.entities.SessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSession(session: SessionEntity)

    @Query("SELECT * FROM monitoring_sessions WHERE sessionId = :sessionId")
    suspend fun getSessionById(sessionId: String): SessionEntity?

    @Query("SELECT * FROM monitoring_sessions ORDER BY startedAt DESC LIMIT 1")
    fun getLatestSessionFlow(): Flow<SessionEntity?>
}
