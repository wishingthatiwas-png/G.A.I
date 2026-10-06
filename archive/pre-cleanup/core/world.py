from dataclasses import dataclass
from time import time

@dataclass
class WorldState:
    last_observation: dict | None = None
    last_change: float = 0.0
    observation_count: int = 0

    def observe(self, observation):
        self.last_observation = observation
        self.last_change = time()
        self.observation_count += 1
