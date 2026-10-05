from __future__ import annotations
from dataclasses import dataclass, asdict
import math, time

@dataclass
class Signal:
    name: str
    value: float = 0.0
    confidence: float = 0.5
    novelty: float = 0.0
    timestamp: float = 0.0

    def emit(self, value: float, confidence: float = 0.5, novelty: float = 0.0):
        self.value = max(-1.0, min(1.0, float(value)))
        self.confidence = max(0.0, min(1.0, float(confidence)))
        self.novelty = max(0.0, min(1.0, float(novelty)))
        self.timestamp = time.time()
        return self

class AdaptiveSignal:
    """Tiny adaptive algorithm: learns an exponentially weighted baseline."""
    def __init__(self, name: str, rate: float = 0.08):
        self.name, self.rate = name, rate
        self.baseline = 0.0
        self.error = 0.0
        self.exposure = 0

    def update(self, value: float):
        value = float(value)
        self.error = value - self.baseline
        self.baseline += self.rate * self.error
        self.exposure += 1
        return Signal(self.name, value, 1.0, min(1.0, abs(self.error)), time.time())

class SignalBus:
    """Simple shared bus. Subsystems publish signals; controllers consume them."""
    def __init__(self):
        self._signals: dict[str, Signal] = {}
        self._adaptive: dict[str, AdaptiveSignal] = {}

    def publish(self, name: str, value: float, confidence=0.5, adaptive=False):
        if adaptive:
            learner = self._adaptive.setdefault(name, AdaptiveSignal(name))
            return self._signals.__setitem__(name, learner.update(value))
        return self._signals.__setitem__(name, Signal(name, value, confidence, 0.0, time.time()))

    def get(self, name: str, default=0.0) -> float:
        return self._signals.get(name, Signal(name, default)).value

    def snapshot(self):
        return {k: asdict(v) for k,v in self._signals.items()}

    def learning_snapshot(self):
        return {k: {"baseline":v.baseline,"error":v.error,"exposure":v.exposure} for k,v in self._adaptive.items()}
