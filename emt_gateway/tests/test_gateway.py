import os
import sqlite3
import unittest
from emt_gateway.run_gateway import EMTGatewayBridge, init_gateway_db, GATEWAY_DB

class TestEMTGatewayBridge(unittest.TestCase):
    def setUp(self):
        init_gateway_db()
        self.bridge = EMTGatewayBridge()

    def tearDown(self):
        if os.path.exists(GATEWAY_DB):
            try:
                os.remove(GATEWAY_DB)
            except Exception:
                pass

    def test_initial_state_no_active_case(self):
        self.assertEqual(self.bridge.state, "NO_ACTIVE_CASE")
        self.assertIsNone(self.bridge.active_case)

    def test_no_data_acquired_before_case_creation(self):
        sample_payload = {
            "event": "VITAL_UPDATE",
            "session_id": "SESSION_001",
            "patient_id": "P001",
            "timestamp": "2026-09-06T10:00:00.000Z",
            "source": "VIRTUAL_CMS8000",
            "data": {
                "heart_rate": {"value": 82, "unit": "bpm"},
                "spo2": {"value": 98, "unit": "%"},
                "pulse_rate": {"value": 82, "unit": "bpm"},
                "blood_pressure": {"systolic": 120, "diastolic": 80, "map": 93, "unit": "mmHg"},
                "respiratory_rate": {"value": 18, "unit": "breaths/min"},
                "temperature": {"t1": {"value": 36.8, "unit": "°C"}, "t2": {"value": 36.9, "unit": "°C"}}
            }
        }
        # Attempting to store while NO_ACTIVE_CASE must be ignored
        self.bridge.store_and_enqueue(sample_payload)
        
        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vital_readings")
        cnt = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(cnt, 0, "No readings should be stored before START CASE")

    def test_create_case_and_start_case_flow(self):
        case = self.bridge.create_case(
            patient_name="John Doe",
            age=42,
            sex="Male",
            classification="Adult"
        )
        self.assertEqual(self.bridge.state, "CREATING_CASE")
        self.assertTrue(case["case_id"].startswith("CASE-"))
        self.assertEqual(case["patient_name"], "John Doe")
        self.assertEqual(case["classification"], "Adult")

        active_case = self.bridge.start_case()
        self.assertEqual(self.bridge.state, "MONITORING_ACTIVE")
        self.assertEqual(active_case["status"], "ACTIVE")

    def test_vital_association_with_active_case(self):
        self.bridge.create_case("Jane Smith", 35, "Female", "Adult")
        self.bridge.start_case()

        sample_payload = {
            "event": "VITAL_UPDATE",
            "session_id": "SESSION_002",
            "patient_id": "P001",
            "timestamp": "2026-09-06T10:05:00.000Z",
            "source": "VIRTUAL_CMS8000",
            "data": {
                "heart_rate": {"value": 90, "unit": "bpm"},
                "spo2": {"value": 97, "unit": "%"},
                "pulse_rate": {"value": 90, "unit": "bpm"},
                "blood_pressure": {"systolic": 118, "diastolic": 76, "map": 90, "unit": "mmHg"},
                "respiratory_rate": {"value": 20, "unit": "breaths/min"},
                "temperature": {"t1": {"value": 37.0, "unit": "°C"}, "t2": {"value": 37.1, "unit": "°C"}}
            }
        }
        self.bridge.store_and_enqueue(sample_payload)

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT case_id, hr, spo2, sys FROM vital_readings")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], self.bridge.active_case["case_id"])
        self.assertEqual(row[1], 90)
        self.assertEqual(row[2], 97)
        self.assertEqual(row[3], 118)

    def test_close_case_and_prevent_data_mixing(self):
        # Case 1
        c1 = self.bridge.create_case("Patient One", 50, "Male", "Adult")
        self.bridge.start_case()
        case1_id = c1["case_id"]

        sample1 = {
            "event": "VITAL_UPDATE", "session_id": "S1", "timestamp": "2026-09-06T10:10:00.000Z",
            "data": {"heart_rate": {"value": 85, "unit": "bpm"}}
        }
        self.bridge.store_and_enqueue(sample1)

        # Close Case 1
        closed = self.bridge.close_case()
        self.assertEqual(closed["status"], "CLOSED")
        self.assertEqual(self.bridge.state, "NO_ACTIVE_CASE")

        # Case 2
        c2 = self.bridge.create_case("Patient Two", 8, "Female", "Pediatric")
        self.bridge.start_case()
        case2_id = c2["case_id"]

        sample2 = {
            "event": "VITAL_UPDATE", "session_id": "S2", "timestamp": "2026-09-06T10:15:00.000Z",
            "data": {"heart_rate": {"value": 110, "unit": "bpm"}}
        }
        self.bridge.store_and_enqueue(sample2)

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT case_id, hr FROM vital_readings WHERE case_id = ?", (case1_id,))
        c1_readings = cursor.fetchall()
        cursor.execute("SELECT case_id, hr FROM vital_readings WHERE case_id = ?", (case2_id,))
        c2_readings = cursor.fetchall()
        conn.close()

        self.assertEqual(len(c1_readings), 1)
        self.assertEqual(c1_readings[0][1], 85)

        self.assertEqual(len(c2_readings), 1)
        self.assertEqual(c2_readings[0][1], 110)

    def test_vital_validation_valid(self):
        valid_vital = {
            "event": "VITAL_UPDATE",
            "patient_id": "P001",
            "session_id": "SESS_TEST",
            "timestamp": "2026-09-05T21:15:32.421Z",
            "source": "VIRTUAL_CMS8000",
            "data": {
                "heart_rate": {"value": 82, "unit": "bpm"},
                "spo2": {"value": 98, "unit": "%"},
                "respiratory_rate": {"value": 18, "unit": "breaths/min"},
                "blood_pressure": {"systolic": 120, "diastolic": 80, "map": 93, "unit": "mmHg"}
            }
        }
        self.assertTrue(self.bridge.validate_vital(valid_vital))

    def test_offline_buffering_and_sync(self):
        self.bridge.create_case("Offline Test", 30, "Male", "Adult")
        self.bridge.start_case()

        self.bridge.is_internet_online = False
        sample_payload = {
            "event": "VITAL_UPDATE", "session_id": "SESS_01", "timestamp": "2026-09-05T21:15:32.421Z",
            "data": {"heart_rate": {"value": 82, "unit": "bpm"}, "spo2": {"value": 98, "unit": "%"}}
        }
        self.bridge.store_and_enqueue(sample_payload)
        self.bridge.process_sync_queue()

        conn = sqlite3.connect(GATEWAY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM sync_queue WHERE status = 'PENDING'")
        pending = cursor.fetchall()
        self.assertEqual(len(pending), 1, "Payload should be pending in offline queue")

        # Restore online & sync
        self.bridge.is_internet_online = True
        self.bridge.process_sync_queue()
        cursor.execute("SELECT status FROM sync_queue WHERE status = 'SYNCED'")
        synced = cursor.fetchall()
        self.assertEqual(len(synced), 1, "Payload should transition to SYNCED when online")
        conn.close()

if __name__ == "__main__":
    unittest.main()
