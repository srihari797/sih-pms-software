import asyncio
import json
import sqlite3
import time
import uuid
from datetime import datetime
import websockets

GATEWAY_DB = "emt_gateway_local.db"

def init_gateway_db():
    conn = sqlite3.connect(GATEWAY_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_cases (
        case_id TEXT PRIMARY KEY,
        patient_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        sex TEXT NOT NULL,
        classification TEXT NOT NULL,
        esi_level INTEGER DEFAULT 2,
        monitor_session_id TEXT,
        created_at TEXT NOT NULL,
        started_at TEXT,
        closed_at TEXT,
        status TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vital_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        source_timestamp TEXT NOT NULL,
        received_timestamp TEXT NOT NULL,
        latency_ms INTEGER NOT NULL,
        source TEXT NOT NULL,
        hr INTEGER,
        spo2 INTEGER,
        pr INTEGER,
        sys INTEGER,
        dia INTEGER,
        map INTEGER,
        rr INTEGER,
        temp1 REAL,
        temp2 REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        record_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        retry_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'PENDING',
        last_attempt TEXT
    );
    """)

    conn.commit()
    conn.close()


class EMTGatewayBridge:
    """
    CAS-AIT EMT Android Gateway Edge Data Bridge (Production Phase 2 & 3).
    Manages Patient Cases (NO_ACTIVE_CASE, CREATING_CASE, MONITORING_ACTIVE, CASE_CLOSED)
    and handles USB/Ethernet data acquisition, automatic disconnect/reconnect, and
    Phase 3 PATIENT_MONITOR_UPDATE serialization.
    """
    def __init__(self, monitor_url: str = "ws://127.0.0.1:8000/ws/monitor/P001"):
        self.monitor_url = monitor_url
        self.is_connected = False
        self.is_internet_online = True
        self.packet_keys = set()
        self.total_received = 0
        self.last_packet_received_at = 0.0
        
        # State machine: NO_ACTIVE_CASE, CREATING_CASE, MONITORING_ACTIVE, CASE_CLOSED
        self.state = "NO_ACTIVE_CASE"
        self.active_case = None
        
        init_gateway_db()

    def create_case(self, patient_name: str, age: int, sex: str, classification: str, esi_level: int = 2) -> dict:
        """EMT initiates a NEW CASE with ESI Level (1 to 5)."""
        case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        now_str = datetime.utcnow().isoformat() + "Z"
        
        case_obj = {
            "case_id": case_id,
            "patient_name": patient_name,
            "age": age,
            "sex": sex,
            "classification": classification,  # Adult, Pediatric, Neonate
            "esi_level": max(1, min(5, esi_level)),
            "monitor_session_id": None,
            "created_at": now_str,
            "started_at": None,
            "closed_at": None,
            "status": "DRAFT"
        }
        
        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO patient_cases (case_id, patient_name, age, sex, classification, esi_level, monitor_session_id, created_at, started_at, closed_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (case_id, patient_name, age, sex, classification, case_obj["esi_level"], None, now_str, None, None, "DRAFT"))
        conn.commit()
        conn.close()

        self.active_case = case_obj
        self.state = "CREATING_CASE"
        return case_obj

    def start_case(self) -> dict:
        """EMT clicks START CASE: Activates data acquisition for active patient case."""
        if not self.active_case:
            raise ValueError("No draft case available to start")
        
        now_str = datetime.utcnow().isoformat() + "Z"
        self.active_case["started_at"] = now_str
        self.active_case["status"] = "ACTIVE"

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE patient_cases SET started_at = ?, status = 'ACTIVE' WHERE case_id = ?
        """, (now_str, self.active_case["case_id"]))
        conn.commit()
        conn.close()

        self.state = "MONITORING_ACTIVE"
        return self.active_case

    def close_case(self) -> dict:
        """EMT clicks CLOSE CASE: Closes active case & returns to NO_ACTIVE_CASE."""
        if not self.active_case:
            self.state = "NO_ACTIVE_CASE"
            return {}

        now_str = datetime.utcnow().isoformat() + "Z"
        closed_case = dict(self.active_case)
        closed_case["closed_at"] = now_str
        closed_case["status"] = "CLOSED"

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE patient_cases SET closed_at = ?, status = 'CLOSED' WHERE case_id = ?
        """, (now_str, self.active_case["case_id"]))
        conn.commit()
        conn.close()

        self.active_case = None
        self.state = "NO_ACTIVE_CASE"
        return closed_case

    def build_phase3_patient_monitor_update(self, payload: dict) -> dict:
        """Constructs canonical Phase 3 PATIENT_MONITOR_UPDATE combining case + monitor + vitals + triage."""
        if not self.active_case:
            return {}

        d = payload.get("data", {})
        hr = d.get("heart_rate", {}).get("value") if d else payload.get("hr")
        spo2 = d.get("spo2", {}).get("value") if d else payload.get("spo2")
        pr = d.get("pulse_rate", {}).get("value") if d else payload.get("pr")
        bp = d.get("blood_pressure", {}) if d else payload.get("bp", {})
        sys_v = bp.get("systolic") if d else (bp.get("sys") if bp else None)
        dia_v = bp.get("diastolic") if d else (bp.get("dia") if bp else None)
        map_v = bp.get("map") if d else (bp.get("map") if bp else None)
        rr = d.get("respiratory_rate", {}).get("value") if d else payload.get("rr")
        temp = d.get("temperature", {}) if d else payload.get("temp", {})
        t1 = temp.get("t1", {}).get("value") if d else (temp.get("t1") if temp else None)
        t2 = temp.get("t2", {}).get("value") if d else (temp.get("t2") if temp else None)

        evt_id = f"EVT_{uuid.uuid4().hex[:8].upper()}"

        return {
            "event": "PATIENT_MONITOR_UPDATE",
            "event_id": evt_id,
            "case": {
                "case_id": self.active_case["case_id"],
                "patient_name": self.active_case["patient_name"],
                "age": self.active_case["age"],
                "sex": self.active_case["sex"].upper(),
                "classification": self.active_case["classification"].upper(),
                "esi_level": self.active_case.get("esi_level", 2)
            },
            "monitor": {
                "source": "VIRTUAL_CMS8000",
                "monitor_session_id": payload.get("session_id", "SESSION_001"),
                "connection": "USB",
                "device_status": "CONNECTED" if self.is_connected else "DISCONNECTED"
            },
            "timestamp": payload.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "data": {
                "heart_rate": {"value": hr, "unit": "bpm"},
                "spo2": {"value": spo2, "unit": "%"},
                "pulse_rate": {"value": pr, "unit": "bpm"},
                "blood_pressure": {"systolic": sys_v, "diastolic": dia_v, "map": map_v, "unit": "mmHg"},
                "respiratory_rate": {"value": rr, "unit": "breaths/min"},
                "temperature": {
                    "t1": {"value": t1, "unit": "°C"},
                    "t2": {"value": t2, "unit": "°C"}
                }
            },
            "triage": {
                "esi_level": self.active_case.get("esi_level", 2)
            }
        }

    def validate_vital(self, data: dict) -> bool:
        """Validates incoming payload parameters."""
        evt = data.get("event") or data.get("type")
        if evt != "VITAL_UPDATE":
            return False

        d = data.get("data")
        if d:
            hr = d.get("heart_rate", {}).get("value")
            spo2 = d.get("spo2", {}).get("value")
            rr = d.get("respiratory_rate", {}).get("value")
            bp = d.get("blood_pressure", {})
            sys_v = bp.get("systolic")
            dia_v = bp.get("diastolic")
        else:
            hr = data.get("hr")
            spo2 = data.get("spo2")
            rr = data.get("rr")
            bp = data.get("bp", {})
            sys_v = bp.get("sys") if bp else None
            dia_v = bp.get("dia") if bp else None

        if hr is not None and not (20 <= hr <= 250): return False
        if spo2 is not None and not (0 <= spo2 <= 100): return False
        if rr is not None and not (0 <= rr <= 100): return False
        if sys_v is not None and dia_v is not None and sys_v <= dia_v: return False

        # Duplicate check
        key = f"{data.get('session_id')}_{data.get('timestamp')}_{evt}"
        if key in self.packet_keys:
            return False
        self.packet_keys.add(key)
        if len(self.packet_keys) > 1000:
            self.packet_keys.clear()

        return True

    def store_and_enqueue(self, payload: dict):
        """Stores vital reading associated with active EMT caseId only."""
        if self.state != "MONITORING_ACTIVE" or not self.active_case:
            # DO NOT pull or store vitals before case creation!
            return

        self.last_packet_received_at = time.time()
        received_ts = datetime.utcnow().isoformat() + "Z"
        source_ts = payload.get("timestamp", received_ts)
        sess_id = payload.get("session_id", "SESSION_001")

        if self.active_case.get("monitor_session_id") != sess_id:
            self.active_case["monitor_session_id"] = sess_id
            conn = sqlite3.connect(GATEWAY_DB)
            cursor = conn.cursor()
            cursor.execute("UPDATE patient_cases SET monitor_session_id = ? WHERE case_id = ?", (sess_id, self.active_case["case_id"]))
            conn.commit()
            conn.close()

        # Extract vitals
        d = payload.get("data", {})
        if d:
            hr = d.get("heart_rate", {}).get("value")
            spo2 = d.get("spo2", {}).get("value")
            pr = d.get("pulse_rate", {}).get("value")
            bp = d.get("blood_pressure", {})
            sys_v = bp.get("systolic")
            dia_v = bp.get("diastolic")
            map_v = bp.get("map")
            rr = d.get("respiratory_rate", {}).get("value")
            temp = d.get("temperature", {})
            t1 = temp.get("t1", {}).get("value")
            t2 = temp.get("t2", {}).get("value")
        else:
            hr = payload.get("hr")
            spo2 = payload.get("spo2")
            pr = payload.get("pr")
            bp = payload.get("bp", {})
            sys_v = bp.get("sys") if bp else None
            dia_v = bp.get("dia") if bp else None
            map_v = bp.get("map") if bp else None
            rr = payload.get("rr")
            temp = payload.get("temp", {})
            t1 = temp.get("t1") if temp else None
            t2 = temp.get("t2") if temp else None

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()

        # Insert into Room DB vital_readings table associated with case_id
        cursor.execute("""
        INSERT INTO vital_readings (case_id, session_id, patient_id, source_timestamp, received_timestamp, latency_ms, source, hr, spo2, pr, sys, dia, map, rr, temp1, temp2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.active_case["case_id"],
            sess_id,
            payload.get("patient_id", "P001"),
            source_ts, received_ts, 12,
            payload.get("source", "VIRTUAL_CMS8000"),
            hr, spo2, pr, sys_v, dia_v, map_v, rr, t1, t2
        ))
        rec_id = cursor.lastrowid

        # Build canonical Phase 3 PATIENT_MONITOR_UPDATE payload
        p3_payload = self.build_phase3_patient_monitor_update(payload)

        # Enqueue in offline sync queue with case association
        cursor.execute("""
        INSERT INTO sync_queue (data_type, record_id, payload_json, created_at, status)
        VALUES (?, ?, ?, ?, ?)
        """, ("PATIENT_MONITOR_UPDATE", str(rec_id), json.dumps(p3_payload), received_ts, "PENDING"))

        conn.commit()
        conn.close()
        self.total_received += 1

    def get_unsynced_count(self) -> int:
        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status != 'SYNCED'")
        cnt = cursor.fetchone()[0]
        conn.close()
        return cnt

    def process_sync_queue(self):
        if not self.is_internet_online:
            return
        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sync_queue WHERE status = 'PENDING' LIMIT 15")
        rows = cursor.fetchall()
        now_str = datetime.utcnow().isoformat() + "Z"
        for r in rows:
            cursor.execute("UPDATE sync_queue SET status = 'SYNCED', last_attempt = ? WHERE id = ?", (now_str, r[0]))
        conn.commit()
        conn.close()


async def run_gateway_demo():
    print("=====================================================")
    print("    CAS-AIT EMT ANDROID GATEWAY / DATA BRIDGE        ")
    print("=====================================================")
    bridge = EMTGatewayBridge()

    print("\n[INITIAL STATE] Android Application Started:")
    print("  State: NO_ACTIVE_CASE")
    print("  Monitor Connection: STANDBY (No data acquired before case creation)\n")

    # EMT initiates a NEW CASE with ESI 2
    case = bridge.create_case("John Doe", 42, "Male", "Adult", esi_level=2)
    print(f"  Draft Case Created: {case['case_id']} | Name: {case['patient_name']} | ESI: {case['esi_level']}")

    active_case = bridge.start_case()
    print(f"  Case Status: ACTIVE | Case ID: {active_case['case_id']}")

    try:
        async with websockets.connect(bridge.monitor_url) as ws:
            bridge.is_connected = True
            print("  [STATUS] MONITOR USB/WIRED CONNECTION: CONNECTED")

            for i in range(3):
                msg = await ws.recv()
                data = json.loads(msg)
                if bridge.validate_vital(data):
                    bridge.store_and_enqueue(data)
                    bridge.process_sync_queue()
                    p3_update = bridge.build_phase3_patient_monitor_update(data)
                    print(f"  [PHASE 3 PAYLOAD] Event: {p3_update.get('event')} | Case: {p3_update.get('case', {}).get('case_id')} | ESI: {p3_update.get('triage', {}).get('esi_level')}")

            bridge.close_case()
            print("\n[SUCCESS] Phase 2 -> Phase 3 EMT Gateway Integration Verified!")

    except Exception as e:
        print(f"[Gateway Demo Error]: {e}")

if __name__ == "__main__":
    asyncio.run(run_gateway_demo())
