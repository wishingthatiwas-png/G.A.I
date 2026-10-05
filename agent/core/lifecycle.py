from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import time

class Phase(str, Enum):
    AWAKE="awake"
    PRE_SLEEP="pre_sleep"
    DREAM="dream"
    WAKE="wake"

@dataclass
class SleepState:
    phase: Phase = Phase.AWAKE
    battery: float = 1.0
    charging: bool = False
    target: float = 1.0
    dream_cycles: int = 0
    dream_latched: bool = False
    reason: str = ""

class Lifecycle:
    """Coordinates operating phases without stopping the core heartbeat."""
    def __init__(self, target=1.0):
        self.state=SleepState(target=target)

    def update_power(self, battery: float, charging: bool):
        self.state.battery=max(0.0,min(1.0,float(battery)))
        self.state.charging=bool(charging)

        if not charging:
            self.state.dream_latched=False
            if self.state.phase in (Phase.PRE_SLEEP,Phase.DREAM):
                self.state.phase=Phase.WAKE
                self.state.reason="charging_stopped"

        elif self.state.battery < max(0.0,self.state.target-0.02):
            self.state.dream_latched=False

        if self.state.phase==Phase.AWAKE and charging and self.state.battery >= 0.20 and not self.state.dream_latched:
            self.state.phase=Phase.PRE_SLEEP
            self.state.reason="charging_and_consolidation_available"
        elif self.state.phase==Phase.DREAM and charging and self.state.battery >= self.state.target:
            self.state.phase=Phase.WAKE
            self.state.dream_latched=True
            self.state.reason="charge_target_reached"

        return self.state

    def enter_dream(self):
        if self.state.phase==Phase.PRE_SLEEP:
            self.state.phase=Phase.DREAM
            self.state.dream_cycles += 1
            self.state.reason="offline_consolidation"
        return self.state

    def finish_wake(self):
        if self.state.phase==Phase.WAKE:
            self.state.phase=Phase.AWAKE
            self.state.reason="awake"
        return self.state
