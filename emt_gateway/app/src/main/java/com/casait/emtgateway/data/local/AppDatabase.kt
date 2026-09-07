package com.casait.emtgateway.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.casait.emtgateway.data.local.entities.EcgEntity
import com.casait.emtgateway.data.local.entities.PatientEntity
import com.casait.emtgateway.data.local.entities.SessionEntity
import com.casait.emtgateway.data.local.entities.SyncQueueEntity
import com.casait.emtgateway.data.local.entities.TriageAssessmentEntity
import com.casait.emtgateway.data.local.entities.VitalEntity

@Database(
    entities = [
        PatientEntity::class,
        SessionEntity::class,
        VitalEntity::class,
        TriageAssessmentEntity::class,
        EcgEntity::class,
        SyncQueueEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun patientDao(): PatientDao
    abstract fun sessionDao(): SessionDao
    abstract fun vitalDao(): VitalDao
    abstract fun triageAssessmentDao(): TriageAssessmentDao
    abstract fun syncQueueDao(): SyncQueueDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // 1. Create patients table
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS patients (
                        patientId TEXT NOT NULL PRIMARY KEY,
                        name TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        sex TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        createdAt TEXT NOT NULL
                    )
                """.trimIndent())

                // 2. Create triage_assessments table
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS triage_assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        assessmentId TEXT NOT NULL,
                        sessionId TEXT NOT NULL,
                        patientId TEXT NOT NULL,
                        vitalReadingId INTEGER NOT NULL,
                        esiLevel INTEGER NOT NULL,
                        generationMethod TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        assessedAt TEXT NOT NULL,
                        FOREIGN KEY(sessionId) REFERENCES monitoring_sessions(sessionId) ON DELETE CASCADE
                    )
                """.trimIndent())
                db.execSQL("CREATE INDEX IF NOT EXISTS index_triage_assessments_sessionId ON triage_assessments(sessionId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_triage_assessments_patientId ON triage_assessments(patientId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_triage_assessments_vitalReadingId ON triage_assessments(vitalReadingId)")

                // 3. Add columns & index to monitoring_sessions
                db.execSQL("ALTER TABLE monitoring_sessions ADD COLUMN ambulanceId TEXT NOT NULL DEFAULT 'AMB-01'")
                db.execSQL("ALTER TABLE monitoring_sessions ADD COLUMN finalEsiLevel INTEGER")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_monitoring_sessions_patientId ON monitoring_sessions(patientId)")

                // 4. Add eventId column & indices to vital_readings
                db.execSQL("ALTER TABLE vital_readings ADD COLUMN eventId TEXT NOT NULL DEFAULT ''")
                db.execSQL("UPDATE vital_readings SET eventId = 'EVT-LEGACY-' || id WHERE eventId = '' OR eventId IS NULL")
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_vital_readings_eventId ON vital_readings(eventId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_vital_readings_sessionId ON vital_readings(sessionId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_vital_readings_patientId ON vital_readings(patientId)")

                // 5. Add chunkId column & indices to ecg_samples
                db.execSQL("ALTER TABLE ecg_samples ADD COLUMN chunkId TEXT NOT NULL DEFAULT ''")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_ecg_samples_sessionId ON ecg_samples(sessionId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_ecg_samples_patientId ON ecg_samples(patientId)")

                // 6. Add lastError column & indices to sync_queue
                db.execSQL("ALTER TABLE sync_queue ADD COLUMN lastError TEXT")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_sync_queue_status ON sync_queue(status)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_sync_queue_createdAt ON sync_queue(createdAt)")
            }
        }

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "emt_gateway.db"
                )
                .addMigrations(MIGRATION_1_2)
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
