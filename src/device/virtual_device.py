import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from src.simulation.scenario_engine import ScenarioEngine
from src.models.vital_reading import VitalReading
from src.models.ecg_sample import ECGSampleChunk
from src.models.sensor_state import SensorState
from src.models.alarm import AlarmEvent

class SensorManager:
    """Manages physical sensor port connections and virtual cable states."""
    def __init__(self, vital_source):
        self.source = vital_source
        self.engine = vital_source.engine

    def get_status(self) -> Dict[str, Any]:
        return self.engine.sensor_state.to_dict()

    def set_connected(self, sensor_name: str, connected: bool) -> Dict[str, Any]:
        state = self.source.set_sensor_connected(sensor_name, connected)
        return state.to_dict()


class AcquisitionEngine:
    """Acquires raw physiological signals (250Hz ECG, 50Hz RESP, 50Hz PLETH)."""
    def __init__(self, vital_source):
        self.source = vital_source

    def get_ecg_chunk(self) -> ECGSampleChunk:
        return self.source.get_ecg_chunk(num_samples=250)

    def get_resp_samples(self, rr: int, connected: bool) -> List[float]:
        return self.source.resp_gen.generate_samples(rr=rr, num_samples=50, connected=connected)

    def get_pleth_samples(self, pr: int, spo2: int, connected: bool) -> List[float]:
        return self.source.pleth_gen.generate_samples(pr=pr, spo2=spo2, num_samples=50, connected=connected)


class ParameterEngine:
    """Processes signals and extracts physiological parameters."""
    def __init__(self, vital_source):
        self.source = vital_source

    def extract_vitals(self) -> VitalReading:
        return self.source.get_latest_vitals()


class AlarmEngine:
    """Evaluates warning/critical thresholds and maintains alarm state."""
    def __init__(self, scenario_engine: ScenarioEngine):
        self.engine = scenario_engine

    def get_active_alarms(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.engine.active_alarms]

    def silence_alarms(self) -> bool:
        for alarm in self.engine.active_alarms:
            alarm.silenced = True
        return True


class TrendManager:
    """Maintains short-term and long-term trend history."""
    def __init__(self, repository):
        self.repository = repository
        self.trend_buffer: List[Dict[str, Any]] = []

    def record_vital(self, vital: VitalReading):
        vital_dict = vital.to_dict()
        self.trend_buffer.append(vital_dict)
        if len(self.trend_buffer) > 3600:  # Keep 1 hour in memory
            self.trend_buffer.pop(0)

    def get_trends(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.trend_buffer[-limit:]


class EventManager:
    """Maintains device event audit log."""
    def __init__(self):
        self.event_log: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, description: str, severity: str = "INFO"):
        event = {
            "id": f"EVT_{uuid.uuid4().hex[:6].upper()}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": event_type,
            "description": description,
            "severity": severity
        }
        self.event_log.append(event)
        if len(self.event_log) > 500:
            self.event_log.pop(0)
        return event

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.event_log[-limit:]


class VirtualCMS8000Device:
    """
    Virtual Contec CMS8000 Patient Monitor Device Architecture.
    Unifies SensorManager, AcquisitionEngine, ParameterEngine, AlarmEngine,
    SessionManager, TrendManager, EventManager, and DataInterface.
    """
    def __init__(self, vital_source, repository):
        self.device_id = "PMS-VIRTUAL-CMS8000-001"
        self.model = "Contec CMS8000 Virtual Patient Monitor"
        self.vital_source = vital_source
        self.repository = repository
        self.engine: ScenarioEngine = vital_source.engine

        self.sensors = SensorManager(self.vital_source)
        self.acquisition = AcquisitionEngine(self.vital_source)
        self.parameters = ParameterEngine(self.vital_source)
        self.alarms = AlarmEngine(self.engine)
        self.trends = TrendManager(repository)
        self.events = EventManager()

        # Device operational state
        self.power_state = "MONITORING"  # OFF, BOOTING, READY, MONITORING
        self.is_frozen = False
        self.alarm_silenced = False

        # Log initial device boot event
        self.events.log_event("POWER_ON", "CMS8000 Virtual Device Booted", "INFO")

    def set_power_state(self, new_state: str) -> Dict[str, Any]:
        self.power_state = new_state
        self.engine.set_power_state(new_state)
        self.events.log_event("POWER_STATE_CHANGE", f"Device state changed to {new_state}", "INFO")
        return self.get_device_status()

    def set_freeze(self, frozen: bool) -> bool:
        self.is_frozen = frozen
        status_str = "FROZEN" if frozen else "RESUMED"
        self.events.log_event("FREEZE_TOGGLE", f"Display waveforms {status_str}", "INFO")
        return self.is_frozen

    def silence_alarms(self) -> bool:
        self.alarm_silenced = True
        self.alarms.silence_alarms()
        self.events.log_event("ALARM_SILENCE", "Audio alarms silenced by user", "WARNING")
        return True

    def trigger_nibp(self) -> Dict[str, Any]:
        result = self.vital_source.trigger_nibp_measurement()
        self.events.log_event("NIBP_TRIGGER", "Manual NIBP measurement started", "INFO")
        return result

    def get_device_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "model": self.model,
            "power_state": self.power_state,
            "session_id": self.engine.session_id,
            "session_status": self.engine.session_status,
            "patient_id": self.engine.patient_id,
            "is_frozen": self.is_frozen,
            "alarm_silenced": self.alarm_silenced,
            "nibp_status": self.engine.nibp_status,
            "sensors": self.sensors.get_status(),
            "active_alarms": self.alarms.get_active_alarms(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
