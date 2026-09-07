import asyncio
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.storage.sqlite import init_db
from src.storage.repositories import PMSRepository
from src.api.routes import router as api_router, vital_source, virtual_device
from src.api.websocket import ws_manager
from src.data.data_serializer import DataSerializer, DataValidator
from src.data.transport.bluetooth_transport import BluetoothTransport
from src.data.transport.transport_manager import transport_manager

# Initialize Bluetooth transport (Server mode listening on RFCOMM channel 1)
bt_transport = BluetoothTransport(mode="SERVER", port=1)
transport_manager.register_transport(bt_transport)

app = FastAPI(title="Contec CMS8000 Virtual Patient Monitor", version="1.0.0")

# Initialize SQLite database
init_db()
repository = PMSRepository()
repository.ensure_patient("P001", "John Doe", 45, "Male", "BED-04")

# Mount API router
app.include_router(api_router)

# Mount Static UI Assets
STATIC_DIR = os.path.join(os.path.dirname(__file__), "src", "ui", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/css", StaticFiles(directory=os.path.join(STATIC_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws/monitor/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: str):
    await ws_manager.connect(websocket)
    try:
        # Send initial canonical status & vitals to connected client
        current_vitals = vital_source.get_latest_vitals()
        sess_id = virtual_device.engine.session_id
        pat_id = virtual_device.engine.patient_id

        device_msg = DataSerializer.build_device_status(
            patient_id=pat_id,
            session_id=sess_id,
            power=(virtual_device.power_state == "MONITORING"),
            monitoring=(virtual_device.power_state == "MONITORING"),
            alarm_active=len(vital_source.engine.active_alarms) > 0,
            freeze=virtual_device.is_frozen
        )
        sensor_msg = DataSerializer.build_sensor_status(
            patient_id=pat_id,
            session_id=sess_id,
            sensor_state=vital_source.engine.sensor_state
        )
        vital_msg = DataSerializer.build_vital_update(
            patient_id=pat_id,
            session_id=sess_id,
            vital_reading=current_vitals,
            sensor_state=vital_source.engine.sensor_state
        )

        await websocket.send_json(DataSerializer.serialize(device_msg))
        await websocket.send_json(DataSerializer.serialize(sensor_msg))
        await websocket.send_json(DataSerializer.serialize(vital_msg))

        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

async def simulation_background_loop():
    """
    Continuous background loop generating 250Hz ECG chunks, RESP waves,
    and 1000ms vital sign updates broadcast via WebSockets & Bluetooth.
    All outgoing payloads strictly conform to canonical Pydantic contracts.
    """
    tick_count = 0
    while True:
        try:
            await asyncio.sleep(1.0)
            tick_count += 1

            session_id = virtual_device.engine.session_id
            patient_id = virtual_device.engine.patient_id

            if vital_source.engine.power_state != "MONITORING":
                # Broadcast device status even when powered off or booting
                device_msg = DataSerializer.build_device_status(
                    patient_id=patient_id,
                    session_id=session_id,
                    power=False,
                    monitoring=False,
                    alarm_active=False,
                    freeze=virtual_device.is_frozen
                )
                await ws_manager.broadcast(DataSerializer.serialize(device_msg))
                transport_manager.broadcast_message(device_msg)
                continue

            # 1. Acquire latest vitals from VitalSource
            vitals = vital_source.get_latest_vitals()

            # 2. Record trend sample
            virtual_device.trends.record_vital(vitals)

            # 3. Validate & build canonical VitalUpdateMessage
            if DataValidator.validate_vital_reading(vitals):
                # Save to SQLite database
                repository.save_vital_reading(vitals)

                # Broadcast canonical VITAL_UPDATE
                vital_msg = DataSerializer.build_vital_update(
                    patient_id=patient_id,
                    session_id=session_id,
                    vital_reading=vitals,
                    sensor_state=vital_source.engine.sensor_state
                )
                await ws_manager.broadcast(DataSerializer.serialize(vital_msg))
                transport_manager.broadcast_message(vital_msg)

            # 4. Broadcast canonical DEVICE_STATUS
            device_msg = DataSerializer.build_device_status(
                patient_id=patient_id,
                session_id=session_id,
                power=True,
                monitoring=True,
                alarm_active=len(vital_source.engine.active_alarms) > 0,
                freeze=virtual_device.is_frozen
            )
            await ws_manager.broadcast(DataSerializer.serialize(device_msg))
            transport_manager.broadcast_message(device_msg)

            # 5. Broadcast canonical SENSOR_STATUS
            sensor_msg = DataSerializer.build_sensor_status(
                patient_id=patient_id,
                session_id=session_id,
                sensor_state=vital_source.engine.sensor_state
            )
            await ws_manager.broadcast(DataSerializer.serialize(sensor_msg))
            transport_manager.broadcast_message(sensor_msg)

            # 6. Acquire ECG 250Hz chunk & broadcast canonical ECG_STREAM
            ecg_chunk = vital_source.get_ecg_chunk(num_samples=250)
            repository.save_ecg_chunk(ecg_chunk)
            ecg_msg = DataSerializer.build_ecg_stream(
                patient_id=patient_id,
                session_id=session_id,
                samples=ecg_chunk.samples,
                lead=ecg_chunk.lead,
                sample_rate_hz=ecg_chunk.sample_rate
            )
            await ws_manager.broadcast(DataSerializer.serialize(ecg_msg))
            transport_manager.broadcast_message(ecg_msg)

            # 7. Acquire RESP & PLETH waveform chunks & broadcast canonical RESP_STREAM & PLETH_STREAM
            resp_samples = vital_source.resp_gen.generate_samples(
                rr=vitals.rr or 0,
                num_samples=50,
                connected=vital_source.engine.sensor_state.ecg
            )
            resp_msg = DataSerializer.build_resp_stream(
                patient_id=patient_id,
                session_id=session_id,
                samples=resp_samples,
                sample_rate_hz=50
            )
            await ws_manager.broadcast(DataSerializer.serialize(resp_msg))
            transport_manager.broadcast_message(resp_msg)

            pleth_samples = vital_source.pleth_gen.generate_samples(
                pr=vitals.pr or 0,
                spo2=vitals.spo2 or 0,
                num_samples=50,
                connected=vital_source.engine.sensor_state.spo2
            )
            pleth_msg = DataSerializer.build_pleth_stream(
                patient_id=patient_id,
                session_id=session_id,
                samples=pleth_samples,
                sample_rate_hz=100
            )
            await ws_manager.broadcast(DataSerializer.serialize(pleth_msg))
            transport_manager.broadcast_message(pleth_msg)

            # 8. Broadcast active alarms if present
            for alarm in vital_source.engine.active_alarms:
                repository.save_alarm_event(alarm)
                alarm_msg = DataSerializer.build_alarm_event(
                    patient_id=patient_id,
                    session_id=session_id,
                    severity=alarm.level,
                    parameter=alarm.parameter,
                    message=alarm.message,
                    active=alarm.active
                )
                await ws_manager.broadcast(DataSerializer.serialize(alarm_msg))
                transport_manager.broadcast_message(alarm_msg)

        except Exception as e:
            print(f"[Simulation Loop Error]: {e}")

@app.on_event("startup")
async def startup_event():
    transport_manager.start_all()
    asyncio.create_task(simulation_background_loop())

@app.on_event("shutdown")
async def shutdown_event():
    transport_manager.stop_all()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

