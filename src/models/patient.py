from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Patient:
    patient_id: str = "P001"
    name: str = "John Doe"
    age: int = 45
    gender: str = "Male"
    bed_no: str = "BED-04"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "bed_no": self.bed_no,
            "created_at": self.created_at
        }
