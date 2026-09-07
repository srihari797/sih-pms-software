import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field


def get_iso_utc_timestamp() -> str:
    """Returns ISO-8601 UTC timestamp format: YYYY-MM-DDTHH:mm:ss.sssZ"""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# Value and Unit Wrappers
class ValueUnitInt(BaseModel):
    value: Optional[int] = None
    unit: str

class ValueUnitFloat(BaseModel):
    value: Optional[float] = None
    unit: str

class BloodPressureData(BaseModel):
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    map: Optional[int] = None
    unit: str = "mmHg"

class TemperatureData(BaseModel):
    t1: ValueUnitFloat
    t2: ValueUnitFloat

class VitalData(BaseModel):
    heart_rate: ValueUnitInt
    spo2: ValueUnitInt
    pulse_rate: ValueUnitInt
    blood_pressure: BloodPressureData
    respiratory_rate: ValueUnitInt
    temperature: TemperatureData


# 1. VITAL_UPDATE
class VitalUpdateMessage(BaseModel):
    event: Literal["VITAL_UPDATE"] = "VITAL_UPDATE"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    data: VitalData


# 2. SENSOR_STATUS
class SensorStateBool(BaseModel):
    connected: bool

class SensorsData(BaseModel):
    ecg: SensorStateBool
    spo2: SensorStateBool
    nibp: SensorStateBool
    temperature_t1: SensorStateBool
    temperature_t2: SensorStateBool

class SensorStatusMessage(BaseModel):
    event: Literal["SENSOR_STATUS"] = "SENSOR_STATUS"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    sensors: SensorsData


# 3. ECG_STREAM
class ECGSignalData(BaseModel):
    lead: str = "II"
    sample_rate_hz: int = 250
    samples: List[float]

class ECGStreamMessage(BaseModel):
    event: Literal["ECG_STREAM"] = "ECG_STREAM"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    signal: ECGSignalData


# 4 & 5. RESP_STREAM & PLETH_STREAM
class WaveformSignalData(BaseModel):
    sample_rate_hz: int
    samples: List[float]

class RespStreamMessage(BaseModel):
    event: Literal["RESP_STREAM"] = "RESP_STREAM"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    signal: WaveformSignalData

class PlethStreamMessage(BaseModel):
    event: Literal["PLETH_STREAM"] = "PLETH_STREAM"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    signal: WaveformSignalData


# 6. ALARM_EVENT
class AlarmData(BaseModel):
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    parameter: str
    message: str
    value: Optional[Union[int, float]] = None
    unit: Optional[str] = None
    active: bool = True

class AlarmEventMessage(BaseModel):
    event: Literal["ALARM_EVENT"] = "ALARM_EVENT"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    alarm: AlarmData


# 7. NIBP_RESULT
class NIBPMeasurementData(BaseModel):
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    map: Optional[int] = None
    unit: str = "mmHg"
    status: Literal["INFLATING", "MEASURING", "COMPLETE", "FAILED", "CANCELLED"]

class NIBPResultMessage(BaseModel):
    event: Literal["NIBP_RESULT"] = "NIBP_RESULT"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    measurement: NIBPMeasurementData


# 8. DEVICE_STATUS
class DeviceStateData(BaseModel):
    power: bool
    monitoring: bool
    alarm_active: bool
    freeze: bool

class DeviceStatusMessage(BaseModel):
    event: Literal["DEVICE_STATUS"] = "DEVICE_STATUS"
    session_id: str
    patient_id: str
    timestamp: str
    source: Literal["VIRTUAL_CMS8000"] = "VIRTUAL_CMS8000"
    device: DeviceStateData


class DataValidator:
    @staticmethod
    def validate_vital_reading(reading) -> bool:
        if reading.hr is not None and not (20 <= reading.hr <= 250):
            return False
        if reading.spo2 is not None and not (30 <= reading.spo2 <= 100):
            return False
        if reading.sys is not None and not (30 <= reading.sys <= 300):
            return False
        if reading.dia is not None and not (20 <= reading.dia <= 200):
            return False
        if reading.rr is not None and not (4 <= reading.rr <= 60):
            return False
        if reading.temp1 is not None and not (25.0 <= reading.temp1 <= 45.0):
            return False
        return True


class DataSerializer:
    @staticmethod
    def build_vital_update(patient_id: str, session_id: str, vital_reading, sensor_state=None) -> VitalUpdateMessage:
        sensors = sensor_state if isinstance(sensor_state, dict) else (sensor_state.to_dict() if hasattr(sensor_state, 'to_dict') else {})
        
        ecg_conn = sensors.get('ecg', True)
        spo2_conn = sensors.get('spo2', True)
        nibp_conn = sensors.get('nibp', True)
        temp1_conn = sensors.get('temp1', True) if 'temp1' in sensors else sensors.get('temperature_t1', True)
        temp2_conn = sensors.get('temp2', True) if 'temp2' in sensors else sensors.get('temperature_t2', True)

        return VitalUpdateMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            data=VitalData(
                heart_rate=ValueUnitInt(
                    value=int(vital_reading.hr) if (ecg_conn and vital_reading.hr is not None) else None,
                    unit="bpm"
                ),
                spo2=ValueUnitInt(
                    value=int(vital_reading.spo2) if (spo2_conn and vital_reading.spo2 is not None) else None,
                    unit="%"
                ),
                pulse_rate=ValueUnitInt(
                    value=int(vital_reading.pr) if (spo2_conn and vital_reading.pr is not None) else None,
                    unit="bpm"
                ),
                blood_pressure=BloodPressureData(
                    systolic=int(vital_reading.sys) if (nibp_conn and vital_reading.sys is not None) else None,
                    diastolic=int(vital_reading.dia) if (nibp_conn and vital_reading.dia is not None) else None,
                    map=int(vital_reading.map) if (nibp_conn and vital_reading.map is not None) else None,
                    unit="mmHg"
                ),
                respiratory_rate=ValueUnitInt(
                    value=int(vital_reading.rr) if (ecg_conn and vital_reading.rr is not None) else None,
                    unit="breaths/min"
                ),
                temperature=TemperatureData(
                    t1=ValueUnitFloat(
                        value=round(float(vital_reading.temp1), 1) if (temp1_conn and vital_reading.temp1 is not None) else None,
                        unit="°C"
                    ),
                    t2=ValueUnitFloat(
                        value=round(float(vital_reading.temp2), 1) if (temp2_conn and vital_reading.temp2 is not None) else None,
                        unit="°C"
                    )
                )
            )
        )

    @staticmethod
    def build_sensor_status(patient_id: str, session_id: str, sensor_state) -> SensorStatusMessage:
        s = sensor_state if isinstance(sensor_state, dict) else (sensor_state.to_dict() if hasattr(sensor_state, 'to_dict') else {})
        return SensorStatusMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            sensors=SensorsData(
                ecg=SensorStateBool(connected=bool(s.get('ecg', True))),
                spo2=SensorStateBool(connected=bool(s.get('spo2', True))),
                nibp=SensorStateBool(connected=bool(s.get('nibp', True))),
                temperature_t1=SensorStateBool(connected=bool(s.get('temp1', True) if 'temp1' in s else s.get('temperature_t1', True))),
                temperature_t2=SensorStateBool(connected=bool(s.get('temp2', True) if 'temp2' in s else s.get('temperature_t2', True)))
            )
        )

    @staticmethod
    def build_ecg_stream(patient_id: str, session_id: str, samples: List[float], lead: str = "II", sample_rate_hz: int = 250) -> ECGStreamMessage:
        return ECGStreamMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            signal=ECGSignalData(
                lead=lead,
                sample_rate_hz=sample_rate_hz,
                samples=[round(float(s), 4) for s in samples]
            )
        )

    @staticmethod
    def build_resp_stream(patient_id: str, session_id: str, samples: List[float], sample_rate_hz: int = 50) -> RespStreamMessage:
        return RespStreamMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            signal=WaveformSignalData(
                sample_rate_hz=sample_rate_hz,
                samples=[round(float(s), 4) for s in samples]
            )
        )

    @staticmethod
    def build_pleth_stream(patient_id: str, session_id: str, samples: List[float], sample_rate_hz: int = 100) -> PlethStreamMessage:
        return PlethStreamMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            signal=WaveformSignalData(
                sample_rate_hz=sample_rate_hz,
                samples=[round(float(s), 4) for s in samples]
            )
        )

    @staticmethod
    def build_alarm_event(patient_id: str, session_id: str, severity: str, parameter: str, message: str, value=None, unit=None, active: bool = True) -> AlarmEventMessage:
        sev_upper = severity.upper()
        if sev_upper not in ["INFO", "WARNING", "CRITICAL"]:
            sev_upper = "WARNING"
        return AlarmEventMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            alarm=AlarmData(
                severity=sev_upper,
                parameter=parameter,
                message=message,
                value=value,
                unit=unit,
                active=active
            )
        )

    @staticmethod
    def build_nibp_result(patient_id: str, session_id: str, systolic: Optional[int], diastolic: Optional[int], map_val: Optional[int], status: str = "COMPLETE") -> NIBPResultMessage:
        stat_upper = status.upper()
        if stat_upper not in ["INFLATING", "MEASURING", "COMPLETE", "FAILED", "CANCELLED"]:
            stat_upper = "COMPLETE"
        return NIBPResultMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            measurement=NIBPMeasurementData(
                systolic=systolic,
                diastolic=diastolic,
                map=map_val,
                unit="mmHg",
                status=stat_upper
            )
        )

    @staticmethod
    def build_device_status(patient_id: str, session_id: str, power: bool, monitoring: bool, alarm_active: bool, freeze: bool) -> DeviceStatusMessage:
        return DeviceStatusMessage(
            session_id=session_id,
            patient_id=patient_id,
            timestamp=get_iso_utc_timestamp(),
            source="VIRTUAL_CMS8000",
            device=DeviceStateData(
                power=power,
                monitoring=monitoring,
                alarm_active=alarm_active,
                freeze=freeze
            )
        )

    @staticmethod
    def serialize(model_obj: BaseModel) -> dict:
        """Validates before serializing to dictionary."""
        if hasattr(model_obj, "model_dump"):
            return model_obj.model_dump(mode="json")
        return model_obj.dict()

    @staticmethod
    def serialize_json(model_obj: BaseModel) -> str:
        """Validates before serializing to JSON string."""
        if hasattr(model_obj, "model_dump_json"):
            return model_obj.model_dump_json()
        return model_obj.json()
