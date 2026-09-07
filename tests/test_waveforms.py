import unittest
from src.waveforms.ecg import ECGGenerator
from src.waveforms.respiration import RespirationGenerator
from src.waveforms.pleth import PlethGenerator

class TestWaveforms(unittest.TestCase):
    def test_ecg_chunk_generation(self):
        gen = ECGGenerator(sample_rate=250)
        samples = gen.generate_samples(hr=82, num_samples=250, ecg_connected=True)
        
        self.assertEqual(len(samples), 250, "Should generate 250 ECG samples")
        max_val = max(samples)
        min_val = min(samples)
        self.assertGreater(max_val, 0.8, "ECG R-wave peak should exceed 0.8 mV")
        self.assertLess(min_val, -0.1, "ECG Q/S wave dip should be negative")

    def test_ecg_lead_off_flatline(self):
        gen = ECGGenerator(sample_rate=250)
        samples = gen.generate_samples(hr=82, num_samples=250, ecg_connected=False)
        
        max_abs = max(abs(s) for s in samples)
        self.assertLess(max_abs, 0.05, "Lead-off ECG should be near flatline")

    def test_resp_and_pleth_generators(self):
        resp_gen = RespirationGenerator(sample_rate=50)
        resp_samples = resp_gen.generate_samples(rr=18, num_samples=50, connected=True)
        self.assertEqual(len(resp_samples), 50)

        pleth_gen = PlethGenerator(sample_rate=50)
        pleth_samples = pleth_gen.generate_samples(pr=82, spo2=98, num_samples=50, connected=True)
        self.assertEqual(len(pleth_samples), 50)

if __name__ == "__main__":
    unittest.main()
