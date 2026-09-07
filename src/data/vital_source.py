from abc import ABC, abstractmethod
from src.models.vital_reading import VitalReading
from src.models.ecg_sample import ECGSampleChunk
from src.models.sensor_state import SensorState

class VitalSource(ABC):
    """
    Abstract Base Class for Patient Monitor Vital Data Sources.
    Provides hardware-decoupled interface for SimulatorVitalSource, RS232VitalSource,
    USBVitalSource, and EthernetVitalSource.
    """

    @abstractmethod
    def get_latest_vitals(self) -> VitalReading:
        pass

    @abstractmethod
    def get_ecg_chunk(self) -> ECGSampleChunk:
        pass

    @abstractmethod
    def get_sensor_status(self) -> SensorState:
        pass

    @abstractmethod
    def set_patient_scenario(self, scenario: str) -> None:
        pass

    @abstractmethod
    def set_sensor_connected(self, sensor_name: str, connected: bool) -> SensorState:
        pass

    @abstractmethod
    def trigger_nibp_measurement(self) -> dict:
        pass

    @abstractmethod
    def get_source_identifier(self) -> str:
        pass
