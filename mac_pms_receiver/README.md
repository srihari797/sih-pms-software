# macOS Native Bluetooth RFCOMM Receiver for PMS

This directory contains the standalone **macOS Native Bluetooth Classic RFCOMM Receiver** for receiving real-time patient vitals, waveforms, alarms, and device status from the Windows PMS Laptop.

---

## 1. Quick Start on Friend's Mac

### Step 1: Pair Devices in System Settings
Before running the receiver, pair your Mac with the Windows PMS laptop in **macOS System Settings -> Bluetooth**.
- Windows PMS Bluetooth MAC Address: `C0:35:32:26:20:18`

### Step 2: Run the Receiver
Open Terminal on your Mac and run:

```bash
python3 mac_receiver.py C0:35:32:26:20:18 5
```
*(Replace `5` with the actual channel reported by the Windows PMS server).*

---

## 2. Options & Features

- **Specify MAC & Channel:**
  ```bash
  python3 mac_receiver.py <MAC_ADDRESS> <CHANNEL>
  ```
- **Raw JSON Debug Mode:**
  Add `--raw` to output raw unparsed JSON payloads:
  ```bash
  python3 mac_receiver.py C0:35:32:26:20:18 5 --raw
  ```

---

## 3. Architecture & Zero Dependencies
- Uses Apple's native `IOBluetooth` framework directly via lightweight native binary (`mac_rfcomm_client.m`) or Swift script (`mac_pms_receiver.swift`).
- Requires **ZERO third-party Python packages** (No PyBluez, PyBluez2, or Bleak needed).
- Message framing uses standard newline-delimited JSON stream boundaries (`\n`).
- Preserves 100% of the canonical JSON schema produced by `DataSerializer`.
