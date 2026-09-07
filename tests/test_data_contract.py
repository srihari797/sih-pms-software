import unittest
import json
import re
from datetime import datetime
from src.data.data_serializer import DataSerializer, VitalUpdateMessage, SensorStatusMessage
from src.data.simulator_source import SimulatorVitalSource
from src.storage.sqlite import init_db
from src.storage.repositories import PMSRepository
from src.device.virtual_device import VirtualCMS8000Device


class TestPMSDataContract(unittest.TestCase):

    def setUp(self):
        init_db()
        self.repository = PMSRepository()
        self.vital_source = SimulatorVitalSource(patient_id="P001")
        self.device = VirtualCMS8000Device(self.vital_source, self.repository)
        self.session_id = self.device.engine.session_id
        self.patient_id = self.device.engine.patient_id

    def test_1_vital_update_root_fields(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)

        self.assertEqual(data_dict["event"], "VITAL_UPDATE")
        self.assertEqual(data_dict["session_id"], self.session_id)
        self.assertEqual(data_dict["patient_id"], self.patient_id)
        self.assertIn("timestamp", data_dict)
        self.assertEqual(data_dict["source"], "VIRTUAL_CMS8000")
        self.assertIn("data", data_dict)

    def test_2_blood_pressure_fields(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)
        bp = data_dict["data"]["blood_pressure"]

        self.assertIn("systolic", bp)
        self.assertIn("diastolic", bp)
        self.assertIn("map", bp)
        self.assertEqual(bp["unit"], "mmHg")

    def test_3_temperature_fields(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)
        temp = data_dict["data"]["temperature"]

        self.assertIn("t1", temp)
        self.assertIn("t2", temp)
        self.assertEqual(temp["t1"]["unit"], "°C")
        self.assertEqual(temp["t2"]["unit"], "°C")

    def test_4_timestamp_iso8601_utc(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)
        ts = data_dict["timestamp"]

        # ISO-8601 UTC regex pattern: YYYY-MM-DDTHH:mm:ss.sssZ
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
        self.assertTrue(re.match(pattern, ts), f"Timestamp {ts} does not match ISO-8601 UTC pattern")

    def test_5_numeric_field_types(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)
        d = data_dict["data"]

        self.assertIsInstance(d["heart_rate"]["value"], int)
        self.assertIsInstance(d["spo2"]["value"], int)
        self.assertIsInstance(d["pulse_rate"]["value"], int)
        self.assertIsInstance(d["blood_pressure"]["systolic"], int)
        self.assertIsInstance(d["blood_pressure"]["diastolic"], int)
        self.assertIsInstance(d["blood_pressure"]["map"], int)
        self.assertIsInstance(d["respiratory_rate"]["value"], int)
        self.assertIsInstance(d["temperature"]["t1"]["value"], float)
        self.assertIsInstance(d["temperature"]["t2"]["value"], float)

    def test_6_no_ui_specific_fields(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        json_str = DataSerializer.serialize_json(msg)
        parsed_dict = json.loads(json_str)
        forbidden_keys = ["camera", "button", "css", "dom", "3d", "layout", "rotation", "zoom", "pan"]
        def check_keys(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    self.assertNotIn(k.lower(), forbidden_keys, f"UI-specific key '{k}' found in JSON output")
                    check_keys(v)
        check_keys(parsed_dict)

    def test_7_valid_json_serialization(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        json_str = DataSerializer.serialize_json(msg)
        parsed = json.loads(json_str)

        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["event"], "VITAL_UPDATE")

    def test_8_changing_patient_state_changes_json_values(self):
        # Normal condition
        self.vital_source.set_patient_scenario("NORMAL")
        normal_vitals = self.vital_source.get_latest_vitals()
        normal_msg = DataSerializer.serialize(DataSerializer.build_vital_update(
            self.patient_id, self.session_id, normal_vitals, self.vital_source.engine.sensor_state
        ))

        # Critical condition
        self.vital_source.set_patient_scenario("CRITICAL")
        critical_vitals = self.vital_source.get_latest_vitals()
        critical_msg = DataSerializer.serialize(DataSerializer.build_vital_update(
            self.patient_id, self.session_id, critical_vitals, self.vital_source.engine.sensor_state
        ))

        self.assertNotEqual(
            normal_msg["data"]["heart_rate"]["value"],
            critical_msg["data"]["heart_rate"]["value"],
            "Heart rate should change between NORMAL and CRITICAL states"
        )
        self.assertNotEqual(
            normal_msg["data"]["spo2"]["value"],
            critical_msg["data"]["spo2"]["value"],
            "SpO2 should change between NORMAL and CRITICAL states"
        )

    def test_9_monitor_display_and_json_values_are_identical(self):
        vitals = self.vital_source.get_latest_vitals()
        msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        data_dict = DataSerializer.serialize(msg)

        self.assertEqual(vitals.hr, data_dict["data"]["heart_rate"]["value"])
        self.assertEqual(vitals.spo2, data_dict["data"]["spo2"]["value"])
        self.assertEqual(vitals.pr, data_dict["data"]["pulse_rate"]["value"])
        self.assertEqual(vitals.sys, data_dict["data"]["blood_pressure"]["systolic"])
        self.assertEqual(vitals.dia, data_dict["data"]["blood_pressure"]["diastolic"])
        self.assertEqual(vitals.map, data_dict["data"]["blood_pressure"]["map"])
        self.assertEqual(vitals.rr, data_dict["data"]["respiratory_rate"]["value"])
        self.assertEqual(round(vitals.temp1, 1), data_dict["data"]["temperature"]["t1"]["value"])

    def test_10_disconnecting_spo2_sensor(self):
        # Disconnect SpO2 sensor
        self.vital_source.set_sensor_connected("spo2", False)
        vitals = self.vital_source.get_latest_vitals()

        vital_msg = DataSerializer.build_vital_update(
            patient_id=self.patient_id,
            session_id=self.session_id,
            vital_reading=vitals,
            sensor_state=self.vital_source.engine.sensor_state
        )
        vital_dict = DataSerializer.serialize(vital_msg)

        # SpO2 value in VITAL_UPDATE must be None (null in JSON)
        self.assertIsNone(vital_dict["data"]["spo2"]["value"])
        self.assertEqual(vital_dict["data"]["spo2"]["unit"], "%")

        # Sensor status event must report spo2 connected: false
        sensor_msg = DataSerializer.build_sensor_status(
            patient_id=self.patient_id,
            session_id=self.session_id,
            sensor_state=self.vital_source.engine.sensor_state
        )
        sensor_dict = DataSerializer.serialize(sensor_msg)

        self.assertEqual(sensor_dict["event"], "SENSOR_STATUS")
        self.assertFalse(sensor_dict["sensors"]["spo2"]["connected"])


if __name__ == "__main__":
    unittest.main()
