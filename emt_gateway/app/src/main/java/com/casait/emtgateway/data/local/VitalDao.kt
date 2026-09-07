package com.casait.emtgateway.data.local

import androidx.room.*
import com.casait.emtgateway.data.local.entities.VitalEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface VitalDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVital(vital: VitalEntity): Long

    @Query("SELECT * FROM vital_readings ORDER BY id DESC LIMIT 1")
    fun getLatestVitalFlow(): Flow<VitalEntity?>

    @Query("SELECT COUNT(*) FROM vital_readings WHERE patientId = :patientId")
    suspend fun getCountByPatient(patientId: String): Int
}
