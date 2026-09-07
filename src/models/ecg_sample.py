from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class ECGSampleChunk:
    patient_id: str
    session_id: str
    lead: str = "II"
    sample_rate: int = 250
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    samples: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "ECG_STREAM",
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "lead": self.lead,
            "sample_rate": self.sample_rate,
            "timestamp": self.timestamp,
            "samples": [round(s, 4) for s in self.samples]
        }
