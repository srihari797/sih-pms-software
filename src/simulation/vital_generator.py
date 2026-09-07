import math
import random
import time
from src.simulation.patient_state import PatientConditionState

SCENARIO_RANGES = {
    PatientConditionState.NORMAL: {
        "hr": (72.0, 86.0), "spo2": (96.0, 99.0), "sys": (112.0, 128.0), "dia": (74.0, 84.0), "rr": (14.0, 20.0), "temp1": (36.5, 37.2)
    },
    PatientConditionState.STRESSED: {
        "hr": (95.0, 114.0), "spo2": (94.0, 97.0), "sys": (130.0, 146.0), "dia": (84.0, 94.0), "rr": (20.0, 26.0), "temp1": (37.0, 37.6)
    },
    PatientConditionState.DETERIORATING: {
        "hr": (115.0, 136.0), "spo2": (86.0, 93.0), "sys": (90.0, 108.0), "dia": (58.0, 68.0), "rr": (25.0, 33.0), "temp1": (37.8, 38.6)
    },
    PatientConditionState.CRITICAL: {
        "hr": (135.0, 154.0), "spo2": (80.0, 86.0), "sys": (78.0, 88.0), "dia": (48.0, 56.0), "rr": (32.0, 38.0), "temp1": (38.6, 39.3)
    },
    PatientConditionState.EMERGENCY: {
        "hr": (152.0, 172.0), "spo2": (72.0, 82.0), "sys": (70.0, 82.0), "dia": (40.0, 48.0), "rr": (36.0, 44.0), "temp1": (39.0, 39.8)
    },
    PatientConditionState.RECOVERY: {
        "hr": (72.0, 86.0), "spo2": (96.0, 99.0), "sys": (112.0, 128.0), "dia": (74.0, 84.0), "rr": (14.0, 20.0), "temp1": (36.5, 37.2)
    }
}

class PhysiologicalVitalGenerator:
    def __init__(self):
        # Initial normal vitals
        self.hr = 82.0
        self.spo2 = 98.0
        self.pr = 82.0
        self.sys = 120.0
        self.dia = 80.0
        self.map_val = 93.3
        self.rr = 18.0
        self.temp1 = 36.8
        self.temp2 = 36.9
        
        self.current_state = PatientConditionState.NORMAL
        self.scenario_ticks = 0

    def set_state(self, state: PatientConditionState):
        """Set active scenario without full instant jump. Blends current vitals 35% toward new scenario target for responsive smooth transition."""
        if state != self.current_state:
            self.current_state = state
            self.scenario_ticks = 0
            bounds = SCENARIO_RANGES[state]
            target_hr = (bounds["hr"][0] + bounds["hr"][1]) / 2.0
            target_spo2 = (bounds["spo2"][0] + bounds["spo2"][1]) / 2.0
            target_sys = (bounds["sys"][0] + bounds["sys"][1]) / 2.0
            target_dia = (bounds["dia"][0] + bounds["dia"][1]) / 2.0
            target_rr = (bounds["rr"][0] + bounds["rr"][1]) / 2.0
            target_t = (bounds["temp1"][0] + bounds["temp1"][1]) / 2.0

            # Initial 35% blend towards target state to initiate smooth transition
            self.hr = self.hr * 0.65 + target_hr * 0.35
            self.spo2 = self.spo2 * 0.65 + target_spo2 * 0.35
            self.sys = self.sys * 0.65 + target_sys * 0.35
            self.dia = self.dia * 0.65 + target_dia * 0.35
            self.rr = self.rr * 0.65 + target_rr * 0.35
            self.temp1 = self.temp1 * 0.65 + target_t * 0.35
            self.temp2 = self.temp1 + 0.1

    def update_tick(self):
        """
        Calculates time-dependent physiological progression on every 1-second tick.
        Moves smoothly from previous current values towards scenario ranges/trends.
        """
        self.scenario_ticks += 1
        bounds = SCENARIO_RANGES[self.current_state]

        min_hr, max_hr = bounds["hr"]
        min_spo2, max_spo2 = bounds["spo2"]
        min_sys, max_sys = bounds["sys"]
        min_dia, max_dia = bounds["dia"]
        min_rr, max_rr = bounds["rr"]
        min_temp, max_temp = bounds["temp1"]

        # --- 1. DETERMINE SCENARIO TARGET VALUES & STEP SPEEDS ---
        if self.current_state == PatientConditionState.DETERIORATING:
            # Progressive deterioration trend over ~20 ticks (20s)
            progress = min(1.0, self.scenario_ticks / 20.0)
            target_hr = min_hr + (max_hr - min_hr) * progress
            target_spo2 = max_spo2 - (max_spo2 - min_spo2) * progress
            target_sys = max_sys - (max_sys - min_sys) * progress
            target_dia = max_dia - (max_dia - min_dia) * progress
            target_rr = min_rr + (max_rr - min_rr) * progress
            target_temp = min_temp + (max_temp - min_temp) * progress
        elif self.current_state == PatientConditionState.RECOVERY:
            # Gradual recovery trend over ~15 ticks (15s) back to normal midpoints
            mid_hr = (min_hr + max_hr) / 2.0
            mid_spo2 = (min_spo2 + max_spo2) / 2.0
            mid_sys = (min_sys + max_sys) / 2.0
            mid_dia = (min_dia + max_dia) / 2.0
            mid_rr = (min_rr + max_rr) / 2.0
            mid_temp = (min_temp + max_temp) / 2.0

            target_hr = self.hr + (mid_hr - self.hr) * 0.25
            target_spo2 = self.spo2 + (mid_spo2 - self.spo2) * 0.25
            target_sys = self.sys + (mid_sys - self.sys) * 0.25
            target_dia = self.dia + (mid_dia - self.dia) * 0.25
            target_rr = self.rr + (mid_rr - self.rr) * 0.25
            target_temp = self.temp1 + (mid_temp - self.temp1) * 0.25
        else:
            # NORMAL, STRESSED, CRITICAL, EMERGENCY:
            # Targets fluctuate within the scenario range
            target_hr = (min_hr + max_hr) / 2.0 + random.uniform(-4.0, 4.0)
            target_spo2 = (min_spo2 + max_spo2) / 2.0 + random.uniform(-1.0, 1.0)
            target_sys = (min_sys + max_sys) / 2.0 + random.uniform(-4.0, 4.0)
            target_dia = (min_dia + max_dia) / 2.0 + random.uniform(-3.0, 3.0)
            target_rr = (min_rr + max_rr) / 2.0 + random.uniform(-2.0, 2.0)
            target_temp = (min_temp + max_temp) / 2.0 + random.uniform(-0.1, 0.1)

        # --- 2. SMOOTH STEPPING TOWARDS TARGETS WITH PHYSIOLOGICAL NOISE ---
        # HR Step (1.5 - 3.5 bpm transition rate)
        if self.hr < target_hr:
            self.hr = min(target_hr, self.hr + random.uniform(1.5, 3.5))
        elif self.hr > target_hr:
            self.hr = max(target_hr, self.hr - random.uniform(1.5, 3.5))
        self.hr += random.choice([-2.0, -1.0, 1.0, 2.0])

        if self.hr >= min_hr and self.hr <= max_hr:
            self.hr = max(min_hr, min(max_hr, self.hr))

        self.pr = self.hr + random.uniform(-0.4, 0.4)

        # SpO2 Step
        if self.spo2 > target_spo2:
            self.spo2 = max(target_spo2, self.spo2 - random.uniform(0.5, 1.2))
        elif self.spo2 < target_spo2:
            self.spo2 = min(target_spo2, self.spo2 + random.uniform(0.5, 1.2))
        self.spo2 += random.choice([-1.0, 0.0, 1.0])

        if self.spo2 >= min_spo2 and self.spo2 <= max_spo2:
            self.spo2 = max(min_spo2, min(max_spo2, self.spo2))

        # SYS / DIA Step
        if self.sys < target_sys:
            self.sys = min(target_sys, self.sys + random.uniform(1.5, 3.0))
        elif self.sys > target_sys:
            self.sys = max(target_sys, self.sys - random.uniform(1.5, 3.0))
        self.sys += random.choice([-2.0, -1.0, 1.0, 2.0])

        if self.sys >= min_sys and self.sys <= max_sys:
            self.sys = max(min_sys, min(max_sys, self.sys))

        if self.dia < target_dia:
            self.dia = min(target_dia, self.dia + random.uniform(1.0, 2.0))
        elif self.dia > target_dia:
            self.dia = max(target_dia, self.dia - random.uniform(1.0, 2.0))
        self.dia += random.choice([-1.5, -0.5, 0.5, 1.5])

        if self.dia >= min_dia and self.dia <= max_dia:
            self.dia = max(min_dia, min(max_dia, self.dia))

        if self.sys <= self.dia + 15.0:
            self.sys = self.dia + 15.0

        self.map_val = self.dia + (self.sys - self.dia) / 3.0

        # RR Step
        if self.rr < target_rr:
            self.rr = min(target_rr, self.rr + random.uniform(0.8, 1.8))
        elif self.rr > target_rr:
            self.rr = max(target_rr, self.rr - random.uniform(0.8, 1.8))
        self.rr += random.choice([-1.0, 0.0, 1.0])

        if self.rr >= min_rr and self.rr <= max_rr:
            self.rr = max(min_rr, min(max_rr, self.rr))

        # TEMP Step
        if self.temp1 < target_temp:
            self.temp1 = min(target_temp, self.temp1 + 0.1)
        elif self.temp1 > target_temp:
            self.temp1 = max(target_temp, self.temp1 - 0.1)
        self.temp1 += random.choice([-0.1, 0.0, 0.1])

        if self.temp1 >= min_temp and self.temp1 <= max_temp:
            self.temp1 = max(min_temp, min(max_temp, self.temp1))
        self.temp2 = round(self.temp1 + 0.1, 1)

        # Print Debug Log on Laptop (Requirement 15)
        now_time = time.strftime("%H:%M:%S")
        v_dict = self.get_vitals_dict()
        print(f"[{now_time}] {self.current_state.value} HR={v_dict['hr']} SpO2={v_dict['spo2']} BP={v_dict['sys']}/{v_dict['dia']} RR={v_dict['rr']} TEMP={v_dict['temp1']}")

    def get_vitals_dict(self) -> dict:
        return {
            "hr": int(round(self.hr)),
            "spo2": int(round(self.spo2)),
            "pr": int(round(self.pr)),
            "sys": int(round(self.sys)),
            "dia": int(round(self.dia)),
            "map": int(round(self.map_val)),
            "rr": int(round(self.rr)),
            "temp1": round(self.temp1, 1),
            "temp2": round(self.temp2, 1)
        }
