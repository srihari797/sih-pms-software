from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SensorState:
    ecg: bool = True
    spo2: bool = True
    nibp: bool = True
    temp1: bool = True
    temp2: bool = True
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return {
            "ecg": self.ecg,
            "spo2": self.spo2,
            "nibp": self.nibp,
            "temp1": self.temp1,
            "temp2": self.temp2,
            "updated_at": self.updated_at
        }
