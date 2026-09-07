package com.casait.emtgateway.data.local

import androidx.room.*
import com.casait.emtgateway.data.local.entities.PatientEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PatientDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPatient(patient: PatientEntity)

    @Query("SELECT * FROM patients WHERE patientId = :patientId")
    suspend fun getPatientById(patientId: String): PatientEntity?

    @Query("SELECT * FROM patients WHERE patientId = :patientId")
    fun getPatientFlow(patientId: String): Flow<PatientEntity?>

    @Query("DELETE FROM patients WHERE patientId = :patientId")
    suspend fun deletePatient(patientId: String)
}
