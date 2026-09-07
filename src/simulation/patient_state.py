from enum import Enum, auto
from dataclasses import dataclass

class PatientConditionState(Enum):
    NORMAL = "NORMAL"
    STRESSED = "STRESSED"
    DETERIORATING = "DETERIORATING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"
    RECOVERY = "RECOVERY"

@dataclass
class TargetVitals:
    hr: float
    spo2: float
    sys: float
    dia: float
    map_val: float
    rr: float
    temp1: float
    temp2: float

STATE_TARGETS = {
    PatientConditionState.NORMAL: TargetVitals(
        hr=82.0, spo2=98.0, sys=120.0, dia=80.0, map_val=93.3, rr=18.0, temp1=36.8, temp2=36.9
    ),
    PatientConditionState.STRESSED: TargetVitals(
        hr=104.0, spo2=95.0, sys=138.0, dia=88.0, map_val=104.7, rr=24.0, temp1=37.3, temp2=37.4
    ),
    PatientConditionState.DETERIORATING: TargetVitals(
        hr=132.0, spo2=87.0, sys=92.0, dia=58.0, map_val=69.3, rr=32.0, temp1=38.4, temp2=38.5
    ),
    PatientConditionState.CRITICAL: TargetVitals(
        hr=144.0, spo2=84.0, sys=82.0, dia=50.0, map_val=60.7, rr=34.0, temp1=39.0, temp2=39.1
    ),
    PatientConditionState.EMERGENCY: TargetVitals(
        hr=158.0, spo2=78.0, sys=75.0, dia=42.0, map_val=53.0, rr=38.0, temp1=39.5, temp2=39.6
    ),
    PatientConditionState.RECOVERY: TargetVitals(
        hr=82.0, spo2=98.0, sys=120.0, dia=80.0, map_val=93.3, rr=18.0, temp1=36.8, temp2=36.9
    ),
}
