import unittest
from src.simulation.patient_state import PatientConditionState
from src.simulation.vital_generator import PhysiologicalVitalGenerator
from src.simulation.scenario_engine import ScenarioEngine

class TestSimulationEngine(unittest.TestCase):
    def test_smooth_vital_transitions(self):
        gen = PhysiologicalVitalGenerator()
        initial_hr = gen.hr
        initial_spo2 = gen.spo2

        # Change state to DETERIORATING
        gen.set_state(PatientConditionState.DETERIORATING)
        
        # Step ticks
        for _ in range(5):
            gen.update_tick()

        # Check gradual changes
        self.assertGreater(gen.hr, initial_hr, "HR should gradually increase in Deteriorating state")
        self.assertLess(gen.spo2, initial_spo2, "SpO2 should gradually decrease in Deteriorating state")

    def test_scenario_engine_alarms(self):
        engine = ScenarioEngine("P001")
        # Trigger critical scenario
        engine.set_scenario("CRITICAL")
        for _ in range(25):
            engine.generator.update_tick()

        vitals = engine.generator.get_vitals_dict()
        alarms = engine.evaluate_backend_alarms(vitals)
        
        self.assertTrue(len(alarms) > 0, "Alarms should trigger during Critical scenario")
        has_critical = any(a.level == "CRITICAL" for a in alarms)
        self.assertTrue(has_critical, "Critical alarm event should be evaluated by backend")

    def test_sensor_state_disconnect(self):
        engine = ScenarioEngine("P001")
        engine.set_sensor("ecg", False)
        self.assertFalse(engine.sensor_state.ecg)
        
        alarms = engine.evaluate_backend_alarms(engine.generator.get_vitals_dict())
        ecg_alarm = any(a.message == "ECG LEAD OFF" for a in alarms)
        self.assertTrue(ecg_alarm, "ECG Lead Off alarm should be generated when sensor is disconnected")

if __name__ == "__main__":
    unittest.main()
