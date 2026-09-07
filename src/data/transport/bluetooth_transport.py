import socket
import threading
import queue
import time
import logging
from typing import Optional

from src.data.transport.transport_interface import TransportInterface

logger = logging.getLogger("PMS_BluetoothTransport")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(ch)


class BluetoothTransport(TransportInterface):
    """
    Bluetooth RFCOMM Transport implementation for PMS.
    
    Transmits newline-delimited JSON payloads over Bluetooth RFCOMM socket.
    Runs entirely in a background worker thread with a non-blocking message queue,
    ensuring main simulation and UI loops never block or freeze if Bluetooth is disconnected.
    """

    def __init__(
        self,
        mode: str = "SERVER",
        target_address: str = "",
        port: int = 1,
        max_queue_size: int = 500
    ):
        """
        :param mode: 'SERVER' (listen for receiver) or 'CLIENT' (connect to target MAC)
        :param target_address: MAC address of target device in CLIENT mode (e.g. 'XX:XX:XX:XX:XX:XX')
        :param port: RFCOMM channel/port (default 1)
        :param max_queue_size: Maximum pending payloads buffer
        """
        self.mode = mode.upper()
        self.target_address = target_address
        self.port = port
        self._send_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        
        self._connected = False
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._active_socket: Optional[socket.socket] = None
        self._server_socket: Optional[socket.socket] = None

    def start(self) -> None:
        """Start the background Bluetooth transport worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="PMS_Bluetooth_Worker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info(f"BluetoothTransport started in {self.mode} mode on RFCOMM channel {self.port}.")

    def stop(self) -> None:
        """Stop background worker and close sockets."""
        self._running = False
        self._connected = False
        self._close_active_socket()
        self._close_server_socket()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        logger.info("BluetoothTransport stopped.")

    def is_connected(self) -> bool:
        """Return True if Bluetooth connection is currently active."""
        return self._connected

    def send(self, payload: str) -> bool:
        """
        Enqueues raw JSON payload string for Bluetooth transmission.
        Non-blocking call. Ensures trailing newline framing '\\n'.
        """
        if not payload:
            return False

        # Ensure string ends with newline framing for stream boundary parsing
        if not payload.endswith("\n"):
            payload += "\n"

        try:
            # Non-blocking put; drop oldest message if queue is full to prevent backpressure
            if self._send_queue.full():
                try:
                    self._send_queue.get_nowait()
                except queue.Empty:
                    pass
            self._send_queue.put_nowait(payload)
            return True
        except Exception as e:
            logger.debug(f"Queue error in BluetoothTransport.send: {e}")
            return False

    def _worker_loop(self) -> None:
        """Main background loop managing connection lifecycle & queue draining."""
        while self._running:
            if not self._connected:
                self._establish_connection()

            if self._connected and self._active_socket:
                self._drain_queue()
            else:
                time.sleep(1.0)

    def _establish_connection(self) -> None:
        """Attempts to establish Bluetooth connection based on configured mode."""
        if self.mode == "SERVER":
            self._run_server_accept()
        else:
            self._run_client_connect()

    def _run_server_accept(self) -> None:
        """Sets up server socket and blocks until a receiver client connects."""
        try:
            if self._server_socket is None:
                # 1. Try native Bluetooth RFCOMM socket first
                if hasattr(socket, "AF_BLUETOOTH"):
                    try:
                        bt_sock = socket.socket(
                            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
                        )
                        # On Windows AF_BLUETOOTH, bind address must be MAC '00:00:00:00:00:00' or BDADDR_ANY
                        bt_sock.bind(("00:00:00:00:00:00", self.port))
                        bt_sock.listen(1)
                        bt_sock.settimeout(2.0)
                        self._server_socket = bt_sock
                        logger.info(f"Bluetooth RFCOMM Server listening on channel {self.port}...")
                    except Exception as bt_err:
                        logger.info(f"Physical Bluetooth RFCOMM unavailable ({bt_err}). Falling back to local test socket (port 8888)...")
                        self._server_socket = None

                # 2. Fallback to TCP socket server for test harness / environment without active BT hardware
                if self._server_socket is None:
                    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    tcp_sock.bind(("0.0.0.0", 8888))
                    tcp_sock.listen(1)
                    tcp_sock.settimeout(2.0)
                    self._server_socket = tcp_sock
                    logger.info("Local test socket server listening on port 8888...")

            while self._running and not self._connected:
                try:
                    client_sock, client_info = self._server_socket.accept()
                    self._active_socket = client_sock
                    self._connected = True
                    logger.info(f"Bluetooth/Test client connected from: {client_info}")
                    break
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.warning(f"Transport accept error: {e}")
                    self._close_server_socket()
                    time.sleep(2.0)
                    break
        except Exception as e:
            logger.error(f"Failed to create transport server socket: {e}")
            self._close_server_socket()
            time.sleep(3.0)

    def _run_client_connect(self) -> None:
        """Connects as client to target MAC address or local test port."""
        if not self.target_address:
            logger.warning("Client mode enabled but target_address is empty.")
            time.sleep(3.0)
            return

        # 1. Try Bluetooth RFCOMM
        if hasattr(socket, "AF_BLUETOOTH"):
            try:
                logger.info(f"Connecting to Bluetooth device {self.target_address} on channel {self.port}...")
                client_sock = socket.socket(
                    socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
                )
                client_sock.settimeout(5.0)
                client_sock.connect((self.target_address, self.port))
                self._active_socket = client_sock
                self._connected = True
                logger.info(f"Connected to Bluetooth device {self.target_address}")
                return
            except Exception as e:
                logger.info(f"Bluetooth connection failed: {e}. Trying test socket fallback...")

        # 2. Fallback to TCP socket
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.settimeout(5.0)
            target_ip = "127.0.0.1" if self.target_address == "00:00:00:00:00:00" else self.target_address
            client_sock.connect((target_ip, 8888))
            self._active_socket = client_sock
            self._connected = True
            logger.info(f"Connected to test socket receiver at {target_ip}:8888")
        except Exception as e:
            logger.warning(f"Transport client connection failed: {e}. Retrying in 3s...")
            self._close_active_socket()
            time.sleep(3.0)

    def _drain_queue(self) -> None:
        """Drains pending JSON payloads from queue and sends over active socket."""
        while self._running and self._connected and self._active_socket:
            try:
                payload = self._send_queue.get(timeout=0.5)
                data_bytes = payload.encode("utf-8")
                self._active_socket.sendall(data_bytes)
                self._send_queue.task_done()
            except queue.Empty:
                continue
            except (socket.error, OSError) as e:
                logger.warning(f"Bluetooth socket send error: {e}. Disconnecting...")
                self._connected = False
                self._close_active_socket()
                break
            except Exception as e:
                logger.error(f"Unexpected error sending Bluetooth payload: {e}")
                self._connected = False
                self._close_active_socket()
                break

    def _close_active_socket(self) -> None:
        if self._active_socket:
            try:
                self._active_socket.close()
            except Exception:
                pass
            self._active_socket = None
        self._connected = False

    def _close_server_socket(self) -> None:
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None
