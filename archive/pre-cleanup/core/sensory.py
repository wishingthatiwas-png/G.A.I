from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class SensoryOrgan:
    organ_id: str
    kind: str
    capabilities: list[str] = field(default_factory=list)
    connected: bool = True
    enabled: bool = True
    sensitivity: float = 1.0
    wake_threshold: float = 0.7
    last_signal: float = 0.0
    last_seen: float = field(default_factory=time.time)

class SensoryDock:
    def __init__(self):
        self.organs: Dict[str, SensoryOrgan] = {}
        self.phase = "awake"
        self.fatigue = 0.0
        self.register("vision.local", "vision", ["camera", "image"])
        self.register("hearing.local", "hearing", ["microphone", "audio"])

    def register(self, organ_id, kind, capabilities=None):
        self.organs[organ_id] = SensoryOrgan(organ_id, kind, capabilities or [])
        return self.organs[organ_id]

    def detach(self, organ_id):
        if organ_id in self.organs:
            self.organs[organ_id].connected = False
            self.organs[organ_id].enabled = False

    def attach(self, organ_id, kind, capabilities=None):
        o = self.organs.get(organ_id) or self.register(organ_id, kind, capabilities)
        o.connected = True
        o.enabled = True
        o.last_seen = time.time()
        return o

    def set_phase(self, phase, fatigue=None):
        self.phase = phase
        if fatigue is not None:
            self.fatigue = max(0.0, min(1.0, float(fatigue)))
        for organ in self.organs.values():
            if not organ.connected:
                continue
            if phase == "awake":
                organ.enabled, organ.sensitivity, organ.wake_threshold = True, 1.0, 0.70
            elif phase == "pre_sleep":
                organ.enabled, organ.sensitivity, organ.wake_threshold = True, 0.35, 0.85
            elif phase == "dream":
                organ.enabled, organ.sensitivity, organ.wake_threshold = False, 0.05, 0.98
            else:
                organ.enabled, organ.sensitivity, organ.wake_threshold = True, 0.10, 0.98
            if self.fatigue < 0.35:
                organ.wake_threshold -= 0.12
            elif self.fatigue > 0.80:
                organ.wake_threshold += 0.08

    def status(self, organ):
        if not organ.connected:
            return "offline"
        if self.phase == "dream" or not organ.enabled:
            return "sleeping"
        if self.phase == "pre_sleep" or organ.sensitivity < 0.5:
            return "fatigued"
        if self.phase == "wake":
            return "recovering"
        return "active"

    def should_wake(self, organ_id, intensity):
        organ = self.organs.get(organ_id)
        # A sleeping organ is inactive for normal sensing, but a strong
        # external signal may still be enough to request wake-up.
        return bool(organ and organ.connected and float(intensity) >= organ.wake_threshold)

    def snapshot(self):
        return {
            "phase": self.phase,
            "fatigue": self.fatigue,
            "organs": {
                key: {**vars(organ), "status": self.status(organ)}
                for key, organ in self.organs.items()
            },
        }
