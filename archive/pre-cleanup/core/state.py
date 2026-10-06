from dataclasses import dataclass, asdict
from time import time

@dataclass
class InternalState:
    energy: float = 1.0
    fatigue: float = 0.0
    sleep_need: float = 0.0
    curiosity: float = 0.5
    boredom: float = 0.0
    stress: float = 0.0
    satisfaction: float = 0.5
    # Ordered affective valence: +1 happiness, 0 neutral, -1 sadness.
    happiness: float = 0.0
    confidence: float = 0.5
    mode: str = "idle"
    uptime: float = 0.0
    last_update: float = 0.0

    def snapshot(self):
        return asdict(self)

    def update_time(self):
        now = time()
        if not self.last_update:
            self.last_update = now
        self.uptime += max(0.0, now - self.last_update)
        self.last_update = now
