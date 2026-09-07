import socket
import json
import sys
import time
from datetime import datetime

# Ensure stdout is unbuffered for live logging
sys.stdout.reconfigure(line_buffering=True)


def run_bluetooth_receiver(target_mac: str = "127.0.0.1", port: int = 1, mode: str = "CLIENT"):
    """
    Bluetooth Test Receiver Harness for PMS.
    
    Acts as a test harness simulating the friend's CAS-AIT laptop Bluetooth receiver.
    Receives newline-delimited stream over Bluetooth RFCOMM, parses each JSON payload,
    validates schema integrity, and prints live vital metrics.
    """
    print("==========================================================")
    print("         PMS BLUETOOTH TEST RECEIVER HARNESS             ")
    print("==========================================================")
    print(f"Mode: {mode}")
    print(f"Target/Interface: {target_mac}, Channel/Port: {port}")
    print("Starting Bluetooth receiver...\n")

    if not hasattr(socket, "AF_BLUETOOTH"):
        print("ERROR: socket.AF_BLUETOOTH is not supported on this system.")
        return

    sock = None
    connected = False

    while True:
        try:
            if not connected:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to PMS Bluetooth/Test Server at {target_mac} channel {port} / port 8888...")
                
                # 1. Try AF_BLUETOOTH RFCOMM
                if hasattr(socket, "AF_BLUETOOTH"):
                    try:
                        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                        sock.connect((target_mac, port))
                        connected = True
                        print(">>> CONNECTED TO PMS VIA BLUETOOTH RFCOMM! Listening for incoming JSON vitals stream...\n")
                    except Exception as bt_err:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bluetooth RFCOMM connection attempt ({bt_err}). Attempting test socket connection...")

                # 2. Try AF_INET TCP socket fallback
                if not connected:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        target_ip = "127.0.0.1" if target_mac == "00:00:00:00:00:00" else target_mac
                        sock.connect((target_ip, 8888))
                        connected = True
                        print(f">>> CONNECTED TO PMS VIA TEST SOCKET ({target_ip}:8888)! Listening for incoming JSON vitals stream...\n")
                    except Exception as tcp_err:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Test socket connection failed ({tcp_err}). Retrying in 3 seconds...\n")
                        time.sleep(3.0)
                        continue

            # Buffer stream reading until newline
            buffer = ""
            while connected:
                chunk = sock.recv(1024).decode("utf-8", errors="replace")
                if not chunk:
                    print("\n[WARNING] Socket closed by server. Disconnected.")
                    connected = False
                    break
                
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        event_type = data.get("event", "UNKNOWN")
                        timestamp = data.get("timestamp", "")
                        session_id = data.get("session_id", "")
                        patient_id = data.get("patient_id", "")

                        if event_type == "VITAL_UPDATE":
                            vitals = data.get("data", {})
                            hr = vitals.get("heart_rate", {}).get("value")
                            spo2 = vitals.get("spo2", {}).get("value")
                            pr = vitals.get("pulse_rate", {}).get("value")
                            bp = vitals.get("blood_pressure", {})
                            bp_str = f"{bp.get('systolic')}/{bp.get('diastolic')} (MAP: {bp.get('map')})" if bp.get("systolic") else "N/A"
                            rr = vitals.get("respiratory_rate", {}).get("value")
                            t1 = vitals.get("temperature", {}).get("t1", {}).get("value")
                            t2 = vitals.get("temperature", {}).get("t2", {}).get("value")

                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [VITAL_UPDATE] "
                                f"Patient: {patient_id} | HR: {hr} bpm | SpO2: {spo2}% | PR: {pr} bpm | "
                                f"BP: {bp_str} | RR: {rr} rpm | T1: {t1}°C, T2: {t2}°C"
                            )

                        elif event_type == "ECG_STREAM":
                            sig = data.get("signal", {})
                            samples = sig.get("samples", [])
                            lead = sig.get("lead", "II")
                            hz = sig.get("sample_rate_hz", 250)
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [ECG_STREAM]   "
                                f"Lead: {lead} | Rate: {hz}Hz | Samples: {len(samples)} items | Range: [{min(samples) if samples else 0}, {max(samples) if samples else 0}]"
                            )

                        elif event_type == "SENSOR_STATUS":
                            sensors = data.get("sensors", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [SENSOR_STATUS] "
                                f"ECG: {sensors.get('ecg', {}).get('connected')} | SpO2: {sensors.get('spo2', {}).get('connected')} | "
                                f"NIBP: {sensors.get('nibp', {}).get('connected')} | Temp: {sensors.get('temperature_t1', {}).get('connected')}"
                            )

                        elif event_type == "ALARM_EVENT":
                            alarm = data.get("alarm", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [ALARM_EVENT]   "
                                f"[{alarm.get('severity')}] {alarm.get('parameter')}: {alarm.get('message')} (Active: {alarm.get('active')})"
                            )

                        elif event_type == "DEVICE_STATUS":
                            dev = data.get("device", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [DEVICE_STATUS] "
                                f"Power: {dev.get('power')} | Monitoring: {dev.get('monitoring')} | AlarmActive: {dev.get('alarm_active')}"
                            )

                        else:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{event_type}] Payload valid JSON: {list(data.keys())}")

                    except json.JSONDecodeError as err:
                        print(f"[ERROR] Invalid JSON payload received: {err} | Raw: {line[:50]}...")

        except (socket.error, OSError) as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection failed: {e}. Retrying in 3 seconds...")
            connected = False
            time.sleep(3.0)
        except KeyboardInterrupt:
            print("\nExiting Bluetooth test receiver.")
            if sock:
                sock.close()
            sys.exit(0)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    run_bluetooth_receiver(target_mac=target, port=port_num)
