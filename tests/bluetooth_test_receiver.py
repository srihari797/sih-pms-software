import socket
import json
import sys
import time
from datetime import datetime

# Ensure stdout is unbuffered for live logging
sys.stdout.reconfigure(line_buffering=True)


def run_bluetooth_receiver(target_mac: str = "127.0.0.1", port: int = 1, raw_debug: bool = False, enable_test_fallback: bool = True):
    """
    Bluetooth Test Receiver Harness for PMS.
    
    Simulates the friend's CAS-AIT Bluetooth receiver.
    Receives newline-delimited stream over physical Bluetooth RFCOMM socket,
    parses each JSON payload, validates schema integrity, and prints live vital metrics.
    """
    print("==========================================================")
    print("         PMS BLUETOOTH TEST RECEIVER HARNESS             ")
    print("==========================================================")
    print(f"Target MAC / Interface: {target_mac}")
    print(f"Configured Channel / Port: {port}")
    print(f"Raw Debug Mode: {raw_debug}")
    print("Starting Bluetooth receiver...\n")

    sock = None
    connected = False

    while True:
        try:
            if not connected:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to PMS Bluetooth Server at MAC={target_mac}, Channel={port}...")
                
                # 1. Physical AF_BLUETOOTH RFCOMM Connection
                if hasattr(socket, "AF_BLUETOOTH") and target_mac != "127.0.0.1":
                    try:
                        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                        sock.connect((target_mac, port))
                        connected = True
                        print(f">>> CONNECTED TO PMS VIA BLUETOOTH RFCOMM (MAC={target_mac}, Channel={port})! Listening for incoming JSON stream...\n")
                    except Exception as bt_err:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Physical Bluetooth RFCOMM connection attempt failed: {bt_err}")
                        if not enable_test_fallback:
                            time.sleep(3.0)
                            continue

                # 2. Local TCP socket fallback ONLY if target is 127.0.0.1 or test fallback enabled
                if not connected and (target_mac == "127.0.0.1" or enable_test_fallback):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        target_ip = "127.0.0.1" if target_mac == "00:00:00:00:00:00" else target_mac
                        sock.connect((target_ip, 8888))
                        connected = True
                        print(f">>> CONNECTED TO PMS VIA TEST SOCKET ({target_ip}:8888)! Listening for incoming JSON stream...\n")
                    except Exception as tcp_err:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection failed ({tcp_err}). Retrying in 3 seconds...\n")
                        time.sleep(3.0)
                        continue

            # Buffer stream reading until newline delimiter
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
                    
                    if raw_debug:
                        print(f"[RAW JSON RECEIVED] {line}")

                    try:
                        data = json.loads(line)
                        event_type = data.get("event", "UNKNOWN")
                        patient_id = data.get("patient_id", "")

                        if event_type == "VITAL_UPDATE":
                            vitals = data.get("data", {})
                            hr = vitals.get("heart_rate", {}).get("value")
                            spo2 = vitals.get("spo2", {}).get("value")
                            pr = vitals.get("pulse_rate", {}).get("value")
                            bp = vitals.get("blood_pressure", {})
                            sys_val = bp.get("systolic")
                            dia_val = bp.get("diastolic")
                            map_val = bp.get("map")
                            bp_str = f"{sys_val}/{dia_val} (MAP: {map_val})" if sys_val else "N/A"
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
                                f"Lead: {lead} | Rate: {hz}Hz | Samples: {len(samples)} items"
                            )

                        elif event_type == "SENSOR_STATUS":
                            sensors = data.get("sensors", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [SENSOR_STATUS] "
                                f"ECG: {sensors.get('ecg', {}).get('connected')} | SpO2: {sensors.get('spo2', {}).get('connected')} | "
                                f"NIBP: {sensors.get('nibp', {}).get('connected')}"
                            )

                        elif event_type == "ALARM_EVENT":
                            alarm = data.get("alarm", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [ALARM_EVENT]   "
                                f"[{alarm.get('severity')}] {alarm.get('parameter')}: {alarm.get('message')}"
                            )

                        elif event_type == "DEVICE_STATUS":
                            dev = data.get("device", {})
                            print(
                                f"[{datetime.now().strftime('%H:%M:%S')}] [DEVICE_STATUS] "
                                f"Power: {dev.get('power')} | Monitoring: {dev.get('monitoring')}"
                            )

                        else:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{event_type}] Valid JSON payload: {list(data.keys())}")

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
    target = "127.0.0.1"
    port_num = 1
    debug_raw = "--raw" in sys.argv or "--raw-debug" in sys.argv

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 0:
        target = args[0]
    if len(args) > 1:
        port_num = int(args[1])

    fallback = (target == "127.0.0.1")
    run_bluetooth_receiver(target_mac=target, port=port_num, raw_debug=debug_raw, enable_test_fallback=fallback)
