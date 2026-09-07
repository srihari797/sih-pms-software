import math
import random
from typing import List

class ECGGenerator:
    def __init__(self, sample_rate: int = 250):
        self.sample_rate = sample_rate
        self.phase = 0.0  # Seconds into current cycle

    def generate_samples(self, hr: int, num_samples: int, ecg_connected: bool = True) -> List[float]:
        if not ecg_connected or hr <= 0:
            # Return flatline with minor line noise
            return [round(random.uniform(-0.02, 0.02), 4) for _ in range(num_samples)]

        cycle_duration = 60.0 / float(hr)
        samples = []

        dt = 1.0 / self.sample_rate
        for _ in range(num_samples):
            t = self.phase % cycle_duration
            norm_t = t / cycle_duration  # 0.0 to 1.0

            # Sum of Gaussian peaks for P-Q-R-S-T waves
            p_wave = 0.15 * math.exp(-((norm_t - 0.18) ** 2) / (2 * (0.025 ** 2)))
            q_wave = -0.15 * math.exp(-((norm_t - 0.35) ** 2) / (2 * (0.012 ** 2)))
            r_wave = 1.25 * math.exp(-((norm_t - 0.38) ** 2) / (2 * (0.015 ** 2)))
            s_wave = -0.28 * math.exp(-((norm_t - 0.42) ** 2) / (2 * (0.014 ** 2)))
            t_wave = 0.32 * math.exp(-((norm_t - 0.68) ** 2) / (2 * (0.055 ** 2)))

            val = p_wave + q_wave + r_wave + s_wave + t_wave
            # Add minor high-frequency muscle baseline noise
            noise = random.uniform(-0.015, 0.015)
            samples.append(round(val + noise, 4))

            self.phase += dt

        return samples
