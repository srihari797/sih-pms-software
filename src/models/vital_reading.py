from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict

@dataclass
class VitalReading:
    patient_id: str
    session_id: str
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    source: str = "SIMULATOR"
    hr: Optional[int] = 82
    spo2: Optional[int] = 98
    pr: Optional[int] = 82
    sys: Optional[int] = 120
    dia: Optional[int] = 80
    map: Optional[int] = 93
    rr: Optional[int] = 18
    temp1: Optional[float] = 36.8
    temp2: Optional[float] = 36.9
    nibp_status: str = "IDLE"  # IDLE, INFLATING, MEASURING, COMPLETE
    sensor_state: Optional[Dict[str, bool]] = None

    def to_dict(self) -> dict:
        return {
            "type": "VITAL_UPDATE",
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "timestamp": self.recorded_at,
            "source": self.source,
            "hr": self.hr if self.sensor_state and self.sensor_state.get("ecg", True) else None,
            "spo2": self.spo2 if self.sensor_state and self.sensor_state.get("spo2", True) else None,
            "pr": self.pr if self.sensor_state and self.sensor_state.get("spo2", True) else None,
            "bp": {
                "sys": self.sys if self.sensor_state and self.sensor_state.get("nibp", True) else None,
                "dia": self.dia if self.sensor_state and self.sensor_state.get("nibp", True) else None,
                "map": self.map if self.sensor_state and self.sensor_state.get("nibp", True) else None,
                "status": self.nibp_status
            },
            "rr": self.rr if self.sensor_state and self.sensor_state.get("ecg", True) else None,
            "temp": {
                "t1": self.temp1 if self.sensor_state and self.sensor_state.get("temp1", True) else None,
                "t2": self.temp2 if self.sensor_state and self.sensor_state.get("temp2", True) else None
            },
            "sensors": self.sensor_state or {}
        }
