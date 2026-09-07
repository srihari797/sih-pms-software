import json
import sqlite3
from typing import List, Optional
from src.storage.sqlite import get_connection, DB_PATH
from src.models.vital_reading import VitalReading
from src.models.ecg_sample import ECGSampleChunk
from src.models.alarm import AlarmEvent

class PMSRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def ensure_patient(self, patient_id: str = "P001", name: str = "John Doe", age: int = 45, gender: str = "Male", bed_no: str = "BED-04"):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO patients (patient_id, name, age, gender, bed_no, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                       (patient_id, name, age, gender, bed_no))
        conn.commit()
        conn.close()

    def upsert_session(self, session_id: str, patient_id: str, started_at: str, ended_at: Optional[str], status: str):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO monitoring_sessions (session_id, patient_id, started_at, ended_at, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET ended_at=excluded.ended_at, status=excluded.status
        """, (session_id, patient_id, started_at, ended_at, status))
        conn.commit()
        conn.close()

    def save_vital_reading(self, reading: VitalReading):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO vital_readings (session_id, patient_id, recorded_at, source, hr, spo2, pr, sys, dia, map, rr, temp1, temp2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reading.session_id, reading.patient_id, reading.recorded_at, reading.source,
            reading.hr, reading.spo2, reading.pr, reading.sys, reading.dia, reading.map, reading.rr,
            reading.temp1, reading.temp2
        ))
        conn.commit()
        conn.close()

    def save_ecg_chunk(self, chunk: ECGSampleChunk):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        samples_json = json.dumps(chunk.samples)
        cursor.execute("""
        INSERT INTO ecg_samples (session_id, patient_id, lead, sample_rate, timestamp, samples)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            chunk.session_id, chunk.patient_id, chunk.lead, chunk.sample_rate, chunk.timestamp, samples_json
        ))
        conn.commit()
        conn.close()

    def save_alarm_event(self, alarm: AlarmEvent):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO alarm_events (session_id, patient_id, timestamp, level, parameter, message, active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alarm.session_id, alarm.patient_id, alarm.timestamp, alarm.level, alarm.parameter, alarm.message, 1 if alarm.active else 0
        ))
        conn.commit()
        conn.close()

    def get_recent_vitals(self, patient_id: str, limit: int = 50) -> List[dict]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT session_id, patient_id, recorded_at, source, hr, spo2, pr, sys, dia, map, rr, temp1, temp2
        FROM vital_readings WHERE patient_id = ? ORDER BY id DESC LIMIT ?
        """, (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            results.append({
                "session_id": r[0], "patient_id": r[1], "recorded_at": r[2], "source": r[3],
                "hr": r[4], "spo2": r[5], "pr": r[6], "sys": r[7], "dia": r[8], "map": r[9],
                "rr": r[10], "temp1": r[11], "temp2": r[12]
            })
        return results
