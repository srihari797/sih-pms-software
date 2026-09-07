import math
import random
from typing import List

class PlethGenerator:
    def __init__(self, sample_rate: int = 50):
        self.sample_rate = sample_rate
        self.phase = 0.0

    def generate_samples(self, pr: int, spo2: int, num_samples: int, connected: bool = True) -> List[float]:
        if not connected or pr <= 0:
            return [round(random.uniform(-0.01, 0.01), 4) for _ in range(num_samples)]

        cycle_duration = 60.0 / float(pr)
        amplitude_scale = max(0.2, min(1.0, spo2 / 100.0))
        samples = []
        dt = 1.0 / self.sample_rate

        for _ in range(num_samples):
            t = self.phase % cycle_duration
            norm_t = t / cycle_duration  # 0.0 to 1.0

            # Systolic peak + dicrotic notch
            sys_peak = math.exp(-((norm_t - 0.25) ** 2) / (2 * (0.06 ** 2)))
            dicrotic = 0.4 * math.exp(-((norm_t - 0.50) ** 2) / (2 * (0.08 ** 2)))
            
            val = (sys_peak + dicrotic) * amplitude_scale
            noise = random.uniform(-0.01, 0.01)
            samples.append(round(val + noise, 4))
            self.phase += dt

        return samples
