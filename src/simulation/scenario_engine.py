import time
import uuid
import asyncio
from typing import Optional, List, Dict
from src.simulation.patient_state import PatientConditionState
from src.simulation.vital_generator import PhysiologicalVitalGenerator
from src.models.sensor_state import SensorState
from src.models.alarm import AlarmEvent

class ScenarioEngine:
    def __init__(self, patient_id: str = "P001"):
        self.patient_id = patient_id
        self.generator = PhysiologicalVitalGenerator()
        self.sensor_state = SensorState()
        
        self.power_state = "MONITORING"  # POWER_OFF, BOOTING, INITIALIZING, MONITORING
        self.session_status = "ACTIVE"   # IDLE, ACTIVE, PAUSED, STOPPED
        self.session_id = f"SESSION_{uuid.uuid4().hex[:8].upper()}"
        self.session_start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.session_end_time: Optional[str] = None
        
        # NIBP state
        self.nibp_status = "IDLE"  # IDLE, INFLATING, MEASURING, COMPLETE
        self.nibp_task_active = False

        # Current active alarms
        self.active_alarms: List[AlarmEvent] = []

    def set_power_state(self, new_state: str):
        self.power_state = new_state
        if new_state == "POWER_OFF":
            self.session_status = "STOPPED"
            self.session_end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        elif new_state == "MONITORING" and self.session_status == "STOPPED":
            self.session_id = f"SESSION_{uuid.uuid4().hex[:8].upper()}"
            self.session_status = "ACTIVE"
            self.session_start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.session_end_time = None

    def set_scenario(self, scenario: str):
        sc_map = {
            "NORMAL": PatientConditionState.NORMAL,
            "STRESSED": PatientConditionState.STRESSED,
            "DETERIORATING": PatientConditionState.DETERIORATING,
            "CRITICAL": PatientConditionState.CRITICAL,
            "EMERGENCY": PatientConditionState.EMERGENCY,
            "RECOVERY": PatientConditionState.RECOVERY
        }
        if scenario.upper() in sc_map:
            self.generator.set_state(sc_map[scenario.upper()])

    def set_sensor(self, sensor_name: str, connected: bool) -> SensorState:
        if hasattr(self.sensor_state, sensor_name.lower()):
            setattr(self.sensor_state, sensor_name.lower(), connected)
        self.sensor_state.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return self.sensor_state

    def trigger_emergency(self):
        self.generator.set_state(PatientConditionState.EMERGENCY)

    def reset_patient(self):
        self.generator = PhysiologicalVitalGenerator()
        self.sensor_state = SensorState()

    async def run_nibp_measurement_async(self):
        """Simulate a 4-second NIBP measurement cuff process."""
        if not self.sensor_state.nibp or self.power_state != "MONITORING":
            return
        self.nibp_status = "INFLATING"
        await asyncio.sleep(1.5)
        self.nibp_status = "MEASURING"
        await asyncio.sleep(2.5)
        self.nibp_status = "COMPLETE"

    def evaluate_backend_alarms(self, vitals: dict) -> List[AlarmEvent]:
        alarms = []
        
        # Sensor disconnect alarms
        if not self.sensor_state.ecg:
            alarms.append(AlarmEvent(self.patient_id, self.session_id, "WARNING", "ECG", "ECG LEAD OFF"))
        if not self.sensor_state.spo2:
            alarms.append(AlarmEvent(self.patient_id, self.session_id, "WARNING", "SpO2", "SpO2 SENSOR OFF"))
        if not self.sensor_state.nibp:
            alarms.append(AlarmEvent(self.patient_id, self.session_id, "INFO", "NIBP", "NIBP NOT CONNECTED"))
        if not self.sensor_state.temp1 and not self.sensor_state.temp2:
            alarms.append(AlarmEvent(self.patient_id, self.session_id, "INFO", "TEMP", "TEMP SENSOR OFF"))

        # Physiological alarms (only evaluate if sensor connected)
        if self.sensor_state.spo2:
            spo2 = vitals.get("spo2", 98)
            if spo2 < 90:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "CRITICAL", "SpO2", f"CRITICAL SpO2: {spo2}%"))
            elif spo2 < 94:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "WARNING", "SpO2", f"LOW SpO2: {spo2}%"))

        if self.sensor_state.ecg:
            hr = vitals.get("hr", 82)
            if hr > 140:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "CRITICAL", "HR", f"TACHYCARDIA: {hr} bpm"))
            elif hr > 120:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "WARNING", "HR", f"HIGH HR: {hr} bpm"))
            elif hr < 50:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "CRITICAL", "HR", f"BRADYCARDIA: {hr} bpm"))

            rr = vitals.get("rr", 18)
            if rr > 30:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "WARNING", "RR", f"TACHYPNEA: {rr} /min"))

        if self.sensor_state.nibp:
            sys = vitals.get("sys", 120)
            if sys < 90:
                alarms.append(AlarmEvent(self.patient_id, self.session_id, "CRITICAL", "BP", f"HYPOTENSION: SYS {sys} mmHg"))

        self.active_alarms = alarms
        return alarms
