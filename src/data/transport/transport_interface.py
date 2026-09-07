from abc import ABC, abstractmethod

class TransportInterface(ABC):
    """
    Abstract interface for data transports in PMS.
    Transports receive raw JSON string payloads produced by DataSerializer
    and transmit them over the underlying medium (e.g. Bluetooth RFCOMM).
    """

    @abstractmethod
    def send(self, payload: str) -> bool:
        """
        Enqueues or sends a JSON payload string over the transport.
        Returns True if accepted into sending pipeline/queue.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Start background connection or transport worker."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop transport worker and close open connections."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if transport currently has an active connection."""
        pass
