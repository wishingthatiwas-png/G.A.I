from __future__ import annotations
from dataclasses import dataclass, asdict
from time import monotonic
import psutil

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(v)))

@dataclass
class CoreNeeds:
    """G.A.I.'s physical/homeostatic condition, derived from its body and environment."""
    power: float = 1.0
    social: float = 0.0
    temperature: float = 0.0
    processing: float = 0.0
    energy: float = 1.0
    rest: float = 0.0
    last_social: float = 0.0
    last_update: float = 0.0

    def update(self, system, hardware=None, now=None):
        now = monotonic() if now is None else float(now)
        dt = 0.0 if not self.last_update else max(0.0, now - self.last_update)
        self.last_update = now

        battery = psutil.sensors_battery()
        if battery is not None:
            self.power = clamp(battery.percent / 100.0)
        else:
            self.power = 1.0

        cores = max(1, int(system.get("cpu_count") or 1))
        load = float(system.get("load_1m") or 0.0)
        self.processing = clamp(load / cores)

        total = float(system.get("memory_total") or 1)
        avail = float(system.get("memory_available") or total)
        memory_pressure = clamp(1.0 - avail / total)

        self.temperature = self._temperature(hardware)
        self.energy = clamp(0.35 * self.power + 0.65 * (1.0 - self.processing))
        self.rest = clamp(self.rest + dt * (0.002 if self.processing > .65 else -0.001))

        # Social need is a slow homeostatic deficit. Actual interaction resets it.
        self.social = clamp(self.social + dt * 0.0015)
        self.social = clamp(self.social + memory_pressure * 0.0002)

        return self

    def register_social(self, strength=1.0):
        self.social = clamp(self.social - 0.35 * clamp(strength))
        self.last_social = monotonic()

    @staticmethod
    def _temperature(hardware):
        # NVIDIA temperature is available when the dGPU is awake; otherwise
        # keep thermal need conservative rather than inventing a reading.
        text = str((hardware or {}).get("nvidia") or "")
        for token in text.replace(",", " ").split():
            try:
                value = float(token)
                if 10 <= value <= 110:
                    return clamp((value - 45.0) / 35.0)
            except ValueError:
                pass
        try:
            temps = psutil.sensors_temperatures()
            values = [x.current for group in temps.values() for x in group
                      if x.current is not None]
            if values:
                value = max(values)
                return clamp((value - 45.0) / 35.0)
        except Exception:
            pass
        return 0.0

    def snapshot(self):
        return asdict(self)
