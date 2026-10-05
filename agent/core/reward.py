from __future__ import annotations
from dataclasses import dataclass, asdict
import time

@dataclass
class RewardSignal:
    name: str
    value: float
    source: str
    timestamp: float

@dataclass
class Drive:
    name: str
    target: float
    weight: float
    reward_rate: float
    decay: float = 0.02
    value: float = 0.0

    def error(self, current: float) -> float:
        return self.target - current

    def reward(self, current: float) -> RewardSignal:
        # Positive reward when movement reduces the drive error.
        err = abs(self.error(current))
        improvement = self.value - err
        self.value = err
        return RewardSignal(self.name, self.reward_rate * improvement, "drive_error", time.time())

class MotivationSystem:
    """Competing drives. Decisions are judged by predicted outcome, not action labels."""
    def __init__(self):
        self.drives = {
            "curiosity": Drive("curiosity", 0.65, 1.0, 0.45),
            "satisfaction": Drive("satisfaction", 0.75, 1.0, 0.55),
            "safety": Drive("safety", 0.15, 1.2, 0.80),
            "energy": Drive("energy", 0.20, 0.8, 0.50),
            "social": Drive("social", 0.35, 0.6, 0.35),
        }
        self.last = {k: 0.0 for k in self.drives}

    def evaluate(self, state) -> dict:
        current = {
            "curiosity": state.curiosity,
            "satisfaction": state.satisfaction,
            "safety": state.stress,
            "energy": state.fatigue,
            "social": 0.0,
        }
        rewards = {}
        for name, drive in self.drives.items():
            r = drive.reward(current[name])
            rewards[name] = asdict(r)
        total = sum(x["value"] * self.drives[x["name"]].weight for x in rewards.values())
        self.last = rewards
        return {"rewards": rewards, "total": total}

    def score_outcome(self, before: dict, after: dict) -> float:
        """Scalar reinforcement signal for the controller."""
        total = 0.0
        for name, drive in self.drives.items():
            b = abs(drive.target - before.get(name, drive.target))
            a = abs(drive.target - after.get(name, drive.target))
            total += drive.weight * drive.reward_rate * (b - a)
        return total
