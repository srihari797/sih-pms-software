import unittest
from fastapi.testclient import TestClient
from main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_current_vitals_endpoint(self):
        response = self.client.get("/api/v1/vitals/current")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hr", data)
        self.assertEqual(data["source"], "SIMULATOR")

    def test_scenario_control(self):
        res = self.client.post("/api/v1/control/scenario", json={"scenario": "STRESSED"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["scenario"], "STRESSED")

    def test_sensor_control(self):
        res = self.client.post("/api/v1/control/sensor", json={"sensor": "ecg", "connected": False})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["sensors"]["ecg"])

    def test_nibp_trigger(self):
        res = self.client.post("/api/v1/control/nibp")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["nibp_state"], "INFLATING")

if __name__ == "__main__":
    unittest.main()
