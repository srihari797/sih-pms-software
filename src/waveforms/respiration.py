import math
import random
from typing import List

class RespirationGenerator:
    def __init__(self, sample_rate: int = 50):
        self.sample_rate = sample_rate
        self.phase = 0.0

    def generate_samples(self, rr: int, num_samples: int, connected: bool = True) -> List[float]:
        if not connected or rr <= 0:
            return [round(random.uniform(-0.01, 0.01), 4) for _ in range(num_samples)]

        cycle_duration = 60.0 / float(rr)
        samples = []
        dt = 1.0 / self.sample_rate

        for _ in range(num_samples):
            t = self.phase % cycle_duration
            norm_t = t / cycle_duration  # 0.0 to 1.0
            
            # Asymmetric sine wave representing inhalation/exhalation
            val = math.sin(2 * math.pi * norm_t)
            if val > 0:
                val = val ** 0.85
            else:
                val = -((-val) ** 1.1)

            noise = random.uniform(-0.02, 0.02)
            samples.append(round(val + noise, 4))
            self.phase += dt

        return samples
