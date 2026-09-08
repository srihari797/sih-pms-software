import os
import sys
import json
import subprocess
import socket
import time
from datetime import datetime

# Ensure stdout is unbuffered for live output
sys.stdout.reconfigure(line_buffering=True)


def parse_and_display_event(json_line: str, raw_debug: bool = False):
    """
    Parses a single newline-delimited JSON line from PMS, validates event type,
    and displays formatted output while keeping the JSON payload 100% untouched.
    """
    if raw_debug:
        print(f"[RAW JSON] {json_line}")

    try:
        data = json.loads(json_line)
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

        elif event_type == "RESP_STREAM":
            sig = data.get("signal", {})
            samples = sig.get("samples", [])
            hz = sig.get("sample_rate_hz", 50)
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] [RESP_STREAM]  "
                f"Rate: {hz}Hz | Samples: {len(samples)} items"
            )

        elif event_type == "PLETH_STREAM":
            sig = data.get("signal", {})
            samples = sig.get("samples", [])
            hz = sig.get("sample_rate_hz", 100)
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] [PLETH_STREAM] "
                f"Rate: {hz}Hz | Samples: {len(samples)} items"
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{event_type}] Valid JSON: {list(data.keys())}")

    except json.JSONDecodeError as err:
        print(f"[ERROR] Invalid JSON line received: {err} | Raw: {json_line[:50]}...")


def start_mac_receiver(target_mac: str, channel: int, raw_debug: bool = False):
    """
    Main entry point for macOS Native RFCOMM Receiver.
    
    1. On macOS: Uses native compiled binary `mac_rfcomm_client` or `swift mac_pms_receiver.swift`.
    2. Cross-platform fallback: Uses native socket (AF_BLUETOOTH) if supported.
    """
    print("==========================================================")
    print("         PMS MACOS NATIVE RFCOMM RECEIVER BRIDGE          ")
    print("==========================================================")
    print(f"Target PMS MAC: {target_mac}")
    print(f"RFCOMM Channel: {channel}")
    print(f"Raw Debug Mode: {raw_debug}")
    print("Starting receiver...\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    native_bin = os.path.join(current_dir, "mac_rfcomm_client")
    swift_script = os.path.join(current_dir, "mac_pms_receiver.swift")
    objc_src = os.path.join(current_dir, "mac_rfcomm_client.m")

    # Check if running on macOS (Darwin)
    is_macos = (sys.platform == "darwin")

    if is_macos:
        # Build native binary if not already compiled
        if not os.path.exists(native_bin) and os.path.exists(objc_src):
            print("[MAC RECEIVER] Compiling native IOBluetooth C binary...")
            try:
                subprocess.run(
                    ["clang", "-O2", "-framework", "IOBluetooth", "-framework", "Foundation", objc_src, "-o", native_bin],
                    check=True
                )
                print("[MAC RECEIVER] Compilation successful!")
            except Exception as e:
                print(f"[MAC RECEIVER] Clang compilation failed: {e}. Will attempt Swift runner.")

        # Launch native process
        cmd = []
        if os.path.exists(native_bin):
            cmd = [native_bin, target_mac, str(channel)]
        elif os.path.exists(swift_script):
            cmd = ["swift", swift_script, target_mac, str(channel)]
        else:
            print("[MAC RECEIVER] ERROR: Neither mac_rfcomm_client binary nor mac_pms_receiver.swift found.")
            return

        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Launching native macOS Bluetooth RFCOMM client: {' '.join(cmd)}")
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, bufsize=1)
                
                buffer = ""
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    line = line.strip()
                    if line:
                        parse_and_display_event(line, raw_debug=raw_debug)

                proc.wait()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Native subprocess exited (code {proc.returncode}). Retrying in 3s...")
                time.sleep(3.0)
            except KeyboardInterrupt:
                print("\nExiting macOS receiver.")
                sys.exit(0)
            except Exception as e:
                print(f"[MAC RECEIVER] Subprocess execution error: {e}. Retrying in 3s...")
                time.sleep(3.0)

    else:
        # Standard AF_BLUETOOTH socket fallback for cross-platform / testing
        print("[MAC RECEIVER] Operating system is not macOS. Using standard AF_BLUETOOTH socket fallback...")
        if not hasattr(socket, "AF_BLUETOOTH"):
            print("[MAC RECEIVER] ERROR: socket.AF_BLUETOOTH is not supported on this host.")
            return

        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to {target_mac} RFCOMM Channel {channel}...")
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                sock.connect((target_mac, channel))
                print(f">>> CONNECTED TO PMS VIA BLUETOOTH RFCOMM (MAC={target_mac}, Channel={channel})!\n")

                buffer = ""
                while True:
                    chunk = sock.recv(1024).decode("utf-8", errors="replace")
                    if not chunk:
                        print("\n[WARNING] Socket closed by remote host. Disconnected.")
                        break
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            parse_and_display_event(line, raw_debug=raw_debug)

                sock.close()
                time.sleep(3.0)
            except KeyboardInterrupt:
                print("\nExiting receiver.")
                sys.exit(0)
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Socket error: {e}. Retrying in 3s...")
                time.sleep(3.0)


if __name__ == "__main__":
    target = "C0:35:32:26:20:18"
    channel_num = 5
    debug_mode = "--raw" in sys.argv or "--raw-debug" in sys.argv

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 0:
        target = args[0]
    if len(args) > 1:
        channel_num = int(args[1])

    start_mac_receiver(target_mac=target, channel=channel_num, raw_debug=debug_mode)
