from datetime import datetime
from src.data.vital_source import VitalSource
from src.simulation.scenario_engine import ScenarioEngine
from src.models.vital_reading import VitalReading
from src.models.ecg_sample import ECGSampleChunk
from src.models.sensor_state import SensorState
from src.waveforms.ecg import ECGGenerator
from src.waveforms.respiration import RespirationGenerator
from src.waveforms.pleth import PlethGenerator

class SimulatorVitalSource(VitalSource):
    """
    Simulator implementation of VitalSource.
    Wraps backend simulation engine, ECG/RESP/PLETH mathematical waveform generators,
    and sensor state.
    """

    def __init__(self, patient_id: str = "P001"):
        self.engine = ScenarioEngine(patient_id=patient_id)
        self.ecg_gen = ECGGenerator(sample_rate=250)
        self.resp_gen = RespirationGenerator(sample_rate=50)
        self.pleth_gen = PlethGenerator(sample_rate=50)

    def get_latest_vitals(self) -> VitalReading:
        # Step simulation engine
        self.engine.generator.update_tick()
        vitals_dict = self.engine.generator.get_vitals_dict()

        reading = VitalReading(
            patient_id=self.engine.patient_id,
            session_id=self.engine.session_id,
            recorded_at=datetime.utcnow().isoformat() + "Z",
            source="SIMULATOR",
            hr=vitals_dict["hr"],
            spo2=vitals_dict["spo2"],
            pr=vitals_dict["pr"],
            sys=vitals_dict["sys"],
            dia=vitals_dict["dia"],
            map=vitals_dict["map"],
            rr=vitals_dict["rr"],
            temp1=vitals_dict["temp1"],
            temp2=vitals_dict["temp2"],
            nibp_status=self.engine.nibp_status,
            sensor_state=self.engine.sensor_state.to_dict()
        )

        # Evaluate alarms
        self.engine.evaluate_backend_alarms(vitals_dict)
        return reading

    def get_ecg_chunk(self, num_samples: int = 250) -> ECGSampleChunk:
        vitals = self.engine.generator.get_vitals_dict()
        samples = self.ecg_gen.generate_samples(
            hr=vitals["hr"],
            num_samples=num_samples,
            ecg_connected=self.engine.sensor_state.ecg
        )
        return ECGSampleChunk(
            patient_id=self.engine.patient_id,
            session_id=self.engine.session_id,
            lead="II",
            sample_rate=250,
            timestamp=datetime.utcnow().isoformat() + "Z",
            samples=samples
        )

    def get_sensor_status(self) -> SensorState:
        return self.engine.sensor_state

    def set_patient_scenario(self, scenario: str) -> None:
        self.engine.set_scenario(scenario)

    def set_sensor_connected(self, sensor_name: str, connected: bool) -> SensorState:
        return self.engine.set_sensor(sensor_name, connected)

    def trigger_nibp_measurement(self) -> dict:
        return {"status": "TRIGGERED", "nibp_state": self.engine.nibp_status}

    def get_source_identifier(self) -> str:
        return "SIMULATOR"
