package com.casait.emtgateway.data.local

import androidx.room.*
import com.casait.emtgateway.data.local.entities.TriageAssessmentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TriageAssessmentDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAssessment(assessment: TriageAssessmentEntity): Long

    @Query("SELECT * FROM triage_assessments WHERE sessionId = :sessionId ORDER BY id DESC")
    suspend fun getAssessmentsBySession(sessionId: String): List<TriageAssessmentEntity>

    @Query("SELECT * FROM triage_assessments WHERE sessionId = :sessionId ORDER BY id DESC LIMIT 1")
    fun getLatestAssessmentFlow(sessionId: String): Flow<TriageAssessmentEntity?>

    @Query("SELECT * FROM triage_assessments WHERE patientId = :patientId ORDER BY id DESC")
    suspend fun getAssessmentsByPatient(patientId: String): List<TriageAssessmentEntity>
}
