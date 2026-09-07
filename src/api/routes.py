import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.data.simulator_source import SimulatorVitalSource
from src.storage.repositories import PMSRepository
from src.device.virtual_device import VirtualCMS8000Device

router = APIRouter(prefix="/api/v1")

# Global singleton vital source and virtual device instances
vital_source = SimulatorVitalSource(patient_id="P001")
repository = PMSRepository()
virtual_device = VirtualCMS8000Device(vital_source, repository)

class ControlPowerRequest(BaseModel):
    state: str  # POWER_OFF, BOOTING, INITIALIZING, MONITORING

class ControlScenarioRequest(BaseModel):
    scenario: str  # NORMAL, STRESSED, DETERIORATING, CRITICAL, EMERGENCY, RECOVERY

class ControlSensorRequest(BaseModel):
    sensor: str  # ecg, spo2, nibp, temp1, temp2
    connected: bool

class ControlFreezeRequest(BaseModel):
    frozen: bool

@router.get("/device/status")
async def get_device_status():
    return virtual_device.get_device_status()

@router.get("/device/trends")
async def get_device_trends(limit: int = 100):
    return virtual_device.trends.get_trends(limit=limit)

@router.get("/device/events")
async def get_device_events(limit: int = 50):
    return virtual_device.events.get_events(limit=limit)

@router.post("/device/freeze")
async def control_freeze(req: ControlFreezeRequest):
    frozen = virtual_device.set_freeze(req.frozen)
    return {"status": "SUCCESS", "is_frozen": frozen}

@router.post("/device/silence")
async def control_silence():
    virtual_device.silence_alarms()
    return {"status": "SUCCESS", "alarm_silenced": True}

@router.post("/device/print")
async def generate_print_report():
    vitals = vital_source.get_latest_vitals().to_dict()
    events = virtual_device.events.get_events(limit=10)
    report = {
        "title": "CONTEC CMS8000 THERMAL STRIP PRINT REPORT",
        "device_id": virtual_device.device_id,
        "patient_id": vital_source.engine.patient_id,
        "timestamp": vitals.get("recorded_at"),
        "vitals": vitals,
        "recent_events": events
    }
    virtual_device.events.log_event("PRINT_STRIP", "Thermal monitoring strip generated", "INFO")
    return report

@router.post("/control/power")
async def control_power(req: ControlPowerRequest):
    res = virtual_device.set_power_state(req.state)
    repository.upsert_session(
        session_id=vital_source.engine.session_id,
        patient_id=vital_source.engine.patient_id,
        started_at=vital_source.engine.session_start_time,
        ended_at=vital_source.engine.session_end_time,
        status=vital_source.engine.session_status
    )
    return {
        "status": "SUCCESS",
        "power_state": vital_source.engine.power_state,
        "session_status": vital_source.engine.session_status,
        "session_id": vital_source.engine.session_id
    }

@router.post("/control/scenario")
async def control_scenario(req: ControlScenarioRequest):
    vital_source.set_patient_scenario(req.scenario)
    virtual_device.events.log_event("SCENARIO_CHANGE", f"Patient scenario changed to {req.scenario}", "WARNING" if req.scenario in ["DETERIORATING", "CRITICAL"] else "INFO")
    return {
        "status": "SUCCESS",
        "scenario": req.scenario,
        "current_state": vital_source.engine.generator.current_state.value
    }

@router.post("/control/sensor")
async def control_sensor(req: ControlSensorRequest):
    updated = virtual_device.sensors.set_connected(req.sensor, req.connected)
    conn_str = "CONNECTED" if req.connected else "DISCONNECTED"
    virtual_device.events.log_event("SENSOR_CHANGE", f"Sensor {req.sensor.upper()} {conn_str}", "WARNING" if not req.connected else "INFO")
    return {
        "status": "SUCCESS",
        "sensor": req.sensor,
        "connected": req.connected,
        "sensors": updated
    }

@router.post("/control/nibp")
async def control_nibp():
    if not vital_source.engine.sensor_state.nibp:
        raise HTTPException(status_code=400, detail="NIBP sensor disconnected")
    
    res = virtual_device.trigger_nibp()
    asyncio.create_task(vital_source.engine.run_nibp_measurement_async())
    return {
        "status": "SUCCESS",
        "message": "NIBP measurement triggered",
        "nibp_state": "INFLATING"
    }

@router.post("/control/emergency")
async def control_emergency():
    vital_source.engine.trigger_emergency()
    virtual_device.events.log_event("EMERGENCY_TRIGGER", "Emergency critical state activated!", "CRITICAL")
    return {"status": "SUCCESS", "message": "Emergency state activated"}

@router.post("/control/reset")
async def control_reset():
    vital_source.engine.reset_patient()
    virtual_device.events.log_event("RESET_PATIENT", "Patient condition reset to Normal", "INFO")
    return {"status": "SUCCESS", "message": "Patient state reset to Normal"}

@router.get("/vitals/current")
async def get_current_vitals():
    reading = vital_source.get_latest_vitals()
    return reading.to_dict()

@router.get("/history")
async def get_history(limit: int = 50):
    return repository.get_recent_vitals("P001", limit=limit)

@router.get("/status")
async def get_status():
    return virtual_device.get_device_status()
