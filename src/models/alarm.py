from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AlarmEvent:
    patient_id: str
    session_id: str
    level: str  # INFO, WARNING, CRITICAL
    parameter: str
    message: str
    active: bool = True
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return {
            "type": "ALARM_EVENT",
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "level": self.level,
            "parameter": self.parameter,
            "message": self.message,
            "active": self.active,
            "timestamp": self.timestamp
        }
