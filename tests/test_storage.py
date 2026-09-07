import os
import unittest
from src.storage.sqlite import init_db
from src.storage.repositories import PMSRepository
from src.models.vital_reading import VitalReading
from src.models.ecg_sample import ECGSampleChunk
from src.models.alarm import AlarmEvent

TEST_DB = "test_pms.db"

class TestStorageRepository(unittest.TestCase):
    def setUp(self):
        init_db(TEST_DB)
        self.repo = PMSRepository(TEST_DB)
        self.repo.ensure_patient("P001", "Jane Doe", 30, "Female", "BED-01")

    def tearDown(self):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_save_and_retrieve_vitals(self):
        reading = VitalReading(
            patient_id="P001",
            session_id="SESS_TEST",
            source="SIMULATOR",
            hr=85,
            spo2=99,
            pr=85,
            sys=122,
            dia=81,
            map=94,
            rr=16,
            temp1=36.7,
            temp2=36.8
        )
        self.repo.save_vital_reading(reading)
        vitals = self.repo.get_recent_vitals("P001", limit=1)
        self.assertEqual(len(vitals), 1)
        self.assertEqual(vitals[0]["hr"], 85)
        self.assertEqual(vitals[0]["source"], "SIMULATOR")

    def test_save_ecg_chunk(self):
        chunk = ECGSampleChunk("P001", "SESS_TEST", lead="II", sample_rate=250, samples=[0.1, 0.2, 1.2, -0.3])
        self.repo.save_ecg_chunk(chunk)

    def test_save_alarm_event(self):
        alarm = AlarmEvent("P001", "SESS_TEST", "CRITICAL", "SpO2", "CRITICAL SpO2: 84%")
        self.repo.save_alarm_event(alarm)

if __name__ == "__main__":
    unittest.main()
