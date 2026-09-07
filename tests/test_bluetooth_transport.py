import unittest
import time
import json

from src.data.transport.bluetooth_transport import BluetoothTransport
from src.data.transport.transport_manager import TransportManager
from src.data.data_serializer import DataSerializer
from src.models.vital_reading import VitalReading


class TestBluetoothTransport(unittest.TestCase):

    def test_bluetooth_transport_initialization(self):
        bt = BluetoothTransport(mode="SERVER", port=1)
        self.assertFalse(bt.is_connected())
        self.assertEqual(bt.mode, "SERVER")
        self.assertEqual(bt.port, 1)

    def test_non_blocking_send_when_disconnected(self):
        bt = BluetoothTransport(mode="SERVER", port=99)
        # Call send without starting worker thread
        payload = '{"event": "TEST", "value": 123}'
        result = bt.send(payload)
        self.assertTrue(result)
        # Queue should contain payload with newline
        self.assertFalse(bt._send_queue.empty())
        item = bt._send_queue.get()
        self.assertTrue(item.endswith("\n"))
        parsed = json.loads(item)
        self.assertEqual(parsed["event"], "TEST")

    def test_transport_manager_broadcast(self):
        manager = TransportManager()
        bt = BluetoothTransport(mode="SERVER", port=99)
        manager.register_transport(bt)

        reading = VitalReading("P001", "S001", hr=75, spo2=98, pr=75, sys=120, dia=80, map=93, rr=16, temp1=36.8, temp2=37.0)
        msg = DataSerializer.build_vital_update("P001", "S001", reading)

        manager.broadcast_message(msg)

        self.assertFalse(bt._send_queue.empty())
        item = bt._send_queue.get()
        data = json.loads(item)
        self.assertEqual(data["event"], "VITAL_UPDATE")
        self.assertEqual(data["patient_id"], "P001")
        self.assertEqual(data["data"]["heart_rate"]["value"], 75)
        self.assertEqual(data["data"]["spo2"]["value"], 98)


if __name__ == "__main__":
    unittest.main()
