import logging
from typing import List, Union, Dict, Any
from pydantic import BaseModel

from src.data.transport.transport_interface import TransportInterface
from src.data.data_serializer import DataSerializer

logger = logging.getLogger("PMS_TransportManager")


class TransportManager:
    """
    Central Manager for outgoing PMS data transports.
    Receives canonical Pydantic messages or raw JSON strings and forwards
    them to all registered external transports (e.g. BluetoothTransport).
    """

    def __init__(self):
        self.transports: List[TransportInterface] = []

    def register_transport(self, transport: TransportInterface) -> None:
        """Register a new transport instance."""
        if transport not in self.transports:
            self.transports.append(transport)
            logger.info(f"Registered transport: {transport.__class__.__name__}")

    def start_all(self) -> None:
        """Start all registered transports."""
        for t in self.transports:
            try:
                t.start()
            except Exception as e:
                logger.error(f"Error starting transport {t}: {e}")

    def stop_all(self) -> None:
        """Stop all registered transports."""
        for t in self.transports:
            try:
                t.stop()
            except Exception as e:
                logger.error(f"Error stopping transport {t}: {e}")

    def broadcast_message(self, message: Union[BaseModel, Dict[str, Any], str]) -> None:
        """
        Broadcasting payload to all registered transports.
        Accepts Pydantic model, dictionary, or raw JSON string.
        """
        if isinstance(message, BaseModel):
            json_str = DataSerializer.serialize_json(message)
        elif isinstance(message, str):
            json_str = message
        elif isinstance(message, dict):
            import json
            json_str = json.dumps(message)
        else:
            logger.warning(f"Unsupported message type: {type(message)}")
            return

        for t in self.transports:
            try:
                t.send(json_str)
            except Exception as e:
                logger.debug(f"Error sending payload to transport {t}: {e}")


# Singleton TransportManager instance for PMS application
transport_manager = TransportManager()
