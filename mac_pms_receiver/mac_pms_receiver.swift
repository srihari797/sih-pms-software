import Foundation
import IOBluetooth

/*
 * Native macOS Swift Bluetooth Classic RFCOMM Receiver for PMS
 *
 * Runs natively on macOS using Apple's IOBluetooth framework.
 * Connects to Windows PMS Laptop Bluetooth MAC address and RFCOMM channel.
 *
 * Compilation / Execution:
 *   swift mac_pms_receiver.swift C0:35:32:26:20:18 5
 *   OR
 *   swiftc mac_pms_receiver.swift -o mac_pms_receiver && ./mac_pms_receiver C0:35:32:26:20:18 5
 */

final class RFCOMMReceiverDelegate: NSObject, IOBluetoothRFCOMMChannelDelegate {
    var isConnected = false

    func rfcommChannelData(_ rfcommChannel: IOBluetoothRFCOMMChannel!, data dataPointer: UnsafeMutableRawPointer!, length dataLength: Int) {
        guard let dataPointer = dataPointer, dataLength > 0 else { return }
        let data = Data(bytes: dataPointer, count: dataLength)
        FileHandle.standardOutput.write(data)
    }

    func rfcommChannelOpenComplete(_ rfcommChannel: IOBluetoothRFCOMMChannel!, status error: IOReturn) {
        if error == kIOReturnSuccess {
            isConnected = true
            fputs("[MAC RFCOMM] >>> CONNECTED TO PMS VIA SWIFT IOBLUETOOTH RFCOMM!\n", stderr)
        } else {
            isConnected = false
            fputs("[MAC RFCOMM] Failed to open RFCOMM channel. Status: \(error)\n", stderr)
            exit(1)
        }
    }

    func rfcommChannelClosed(_ rfcommChannel: IOBluetoothRFCOMMChannel!) {
        isConnected = false
        fputs("\n[MAC RFCOMM] [WARNING] RFCOMM channel closed by remote host.\n", stderr)
        exit(0)
    }
}

func main() {
    let args = CommandLine.arguments
    guard args.count >= 3 else {
        fputs("Usage: swift mac_pms_receiver.swift <MAC_ADDRESS> <CHANNEL>\n", stderr)
        fputs("Example: swift mac_pms_receiver.swift C0:35:32:26:20:18 5\n", stderr)
        exit(1)
    }

    let macArg = args[1].replacingOccurrences(of: ":", with: "-")
    guard let channelID = UInt8(args[2]) else {
        fputs("Invalid RFCOMM Channel number.\n", stderr)
        exit(1)
    }

    fputs("[MAC RFCOMM] Connecting to PMS Bluetooth MAC=\(macArg) CHANNEL=\(channelID)...\n", stderr)

    guard let device = IOBluetoothDevice(addressString: macArg) else {
        fputs("[MAC RFCOMM] ERROR: Could not find paired Bluetooth device for MAC: \(macArg)\n", stderr)
        exit(1)
    }

    let delegate = RFCOMMReceiverDelegate()
    var rfcommChannel: IOBluetoothRFCOMMChannel?

    let status = device.openRFCOMMChannelSync(&rfcommChannel, withChannelID: channelID, delegate: delegate)
    guard status == kIOReturnSuccess, rfcommChannel != nil else {
        fputs("[MAC RFCOMM] Failed to open RFCOMM channel sync: \(status)\n", stderr)
        exit(1)
    }

    RunLoop.current.run()
}

main()
