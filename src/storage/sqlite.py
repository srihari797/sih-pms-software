import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pms_data.db")

def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        bed_no TEXT,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitoring_sessions (
        session_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vital_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        source TEXT NOT NULL,
        hr INTEGER,
        spo2 INTEGER,
        pr INTEGER,
        sys INTEGER,
        dia INTEGER,
        map INTEGER,
        rr INTEGER,
        temp1 REAL,
        temp2 REAL,
        FOREIGN KEY (session_id) REFERENCES monitoring_sessions (session_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ecg_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        lead TEXT NOT NULL,
        sample_rate INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        samples TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES monitoring_sessions (session_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alarm_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        parameter TEXT NOT NULL,
        message TEXT NOT NULL,
        active INTEGER NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def get_connection(db_path: str = DB_PATH):
    return sqlite3.connect(db_path)
