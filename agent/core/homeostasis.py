from __future__ import annotations
from dataclasses import dataclass, asdict
from time import monotonic
import psutil
import shutil

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
    sleep_need: float = 0.0
    storage_pressure: float = 0.0
    storage_sleep_need: float = 0.0
    memory_pressure: float = 0.0
    memory_sleep_need: float = 0.0
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

        try:
            usage = shutil.disk_usage("/mnt/gai")
            used_ratio = usage.used / max(1, usage.total)
            # Storage is G.A.I.'s sleep analogue: high utilisation creates a
            # consolidation/deep-storage pressure, but does not force sleep in V1.
            self.storage_pressure = clamp((used_ratio - 0.70) / 0.25)
        except Exception:
            self.storage_pressure = 0.0

        self.storage_sleep_need = clamp(self.storage_pressure * 0.9)
        persistent_usage = clamp(float(system.get("persistent_memory_usage", 0.0) or 0.0))
        self.memory_pressure = clamp((persistent_usage - 0.50) / 0.40)
        self.memory_sleep_need = clamp(self.memory_pressure * 0.95)
        self.storage_sleep_need = max(self.storage_sleep_need, self.memory_sleep_need)

        self.temperature = self._temperature(hardware)
        self.energy = clamp(0.35 * self.power + 0.65 * (1.0 - self.processing))

        # Rest is a true accumulating homeostatic deficit. Low energy and time
        # awake increase the need; heavy processing accelerates it. Sleep/rest
        # is handled by the lifecycle and drains this need when the system is
        # actually resting rather than merely being idle.
        low_energy = 1.0 - self.energy
        rest_drive = 0.0012 + 0.0035 * low_energy + 0.0025 * self.processing
        self.rest = clamp(self.rest + dt * rest_drive)
        # Lifecycle owns the sleep clock; homeostasis exposes it as a body need.
        lifecycle_need = system.get("sleep_need")
        if lifecycle_need is not None:
            self.sleep_need = max(clamp(lifecycle_need), self.storage_sleep_need)

        # When the machine is genuinely resting, discharge the accumulated
        # need instead of merely letting fatigue and rest stay high forever.
        phase = str(system.get("lifecycle_phase") or "awake").lower()
        if phase in {"pre_sleep", "dream", "sleep"}:
            self.rest = clamp(self.rest - dt * 0.012)

        # Social need is a slow homeostatic deficit. Actual interaction resets it.
        self.social = clamp(self.social + dt * 0.0015)
        self.social = clamp(self.social + memory_pressure * 0.0002)

        return self

    def register_social(self, strength=1.0):
        self.social = clamp(self.social - 0.35 * clamp(strength))
        self.last_social = monotonic()

    def register_rest(self, strength=1.0):
        """Discharge accumulated rest debt when the organism deliberately rests."""
        amount = clamp(strength)
        self.rest = clamp(self.rest - 0.20 * amount)
        self.last_update = monotonic()

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
