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
    awake_ticks: int = 0
    sleep_ticks: int = 0
    sleep_need: float = 0.0

class Lifecycle:
    """Coordinates operating phases without stopping the core heartbeat."""
    def __init__(self, target=1.0):
        self.state=SleepState(target=target)

    def update_power(self, battery: float, charging: bool, energy: float | None = None, fatigue: float | None = None, memory_pressure: float = 0.0):
        # Biological sleep clock: 10,000 awake base ticks, then a short 1,000-tick nap.
        # The clock is scaled by metabolic workers so faster metabolism reaches sleep
        # proportionally sooner in real time while preserving the same tick counts.
        workers = max(1, int(getattr(self, "metabolic_workers", 1)))
        awake_limit = 10000 * workers
        nap_limit = 1000 * workers
        # Tick counters advance from the core scheduler, not this slower
        # power/lifecycle check. That makes the sleep clock a real tick clock.
        # See clock_tick() below.
        self.state.battery=max(0.0,min(1.0,float(battery)))
        self.state.charging=bool(charging)
        internal_energy = None if energy is None else max(0.0, min(1.0, float(energy)))
        internal_fatigue = None if fatigue is None else max(0.0, min(1.0, float(fatigue)))
        # Charging alone is not a reason to sleep. If the organism has plenty of
        # internal energy and is not badly fatigued, stay awake and use the surplus.
        energetic_enough_to_stay_awake = (
            internal_energy is not None and internal_energy >= 0.80 and
            (internal_fatigue is None or internal_fatigue < 0.70)
        )

        if not charging:
            self.state.dream_latched=False
            if self.state.phase in (Phase.PRE_SLEEP,Phase.DREAM):
                self.state.phase=Phase.WAKE
                self.state.reason="charging_stopped"

        elif self.state.battery < max(0.0,self.state.target-0.02):
            self.state.dream_latched=False

        battery_sleepiness = max(0.0, min(1.0, (0.45 - self.state.battery) / 0.45))
        clock_sleep = self.state.sleep_need >= 0.98
        low_battery_sleep = battery_sleepiness >= 0.55 and not energetic_enough_to_stay_awake
        memory_consolidation_needed = memory_pressure >= 0.80

        if self.state.phase==Phase.AWAKE and (low_battery_sleep or clock_sleep):
            self.state.phase=Phase.PRE_SLEEP
            self.state.reason="sleep_clock" if clock_sleep else "battery_low_sleepiness"
        elif (self.state.phase==Phase.AWAKE and charging and self.state.battery >= 0.20
                and not self.state.dream_latched and (memory_consolidation_needed or not energetic_enough_to_stay_awake)):
            self.state.phase=Phase.PRE_SLEEP
            self.state.reason="memory_pressure_consolidation"
        elif self.state.phase in (Phase.PRE_SLEEP, Phase.DREAM) and energetic_enough_to_stay_awake:
            self.state.phase=Phase.WAKE
            self.state.dream_latched=False
            self.state.reason="energy_available_stay_awake"
        elif self.state.phase==Phase.DREAM and charging and self.state.battery >= self.state.target:
            self.state.phase=Phase.WAKE
            self.state.dream_latched=True
            self.state.reason="charge_target_reached"

        return self.state

    def clock_tick(self):
        workers = max(1, int(getattr(self, "metabolic_workers", 1)))
        awake_limit = 10000 * workers
        nap_limit = 1000 * workers
        if self.state.phase == Phase.AWAKE:
            self.state.awake_ticks += 1
            progress = min(1.0, self.state.awake_ticks / awake_limit)
            self.state.sleep_need = progress ** 4
        elif self.state.phase == Phase.DREAM:
            self.state.sleep_ticks += 1
            nap_progress = min(1.0, self.state.sleep_ticks / nap_limit)
            self.state.sleep_need = max(0.0, 1.0 - nap_progress)
            if self.state.sleep_ticks >= nap_limit:
                self.state.phase = Phase.WAKE
                self.state.reason = "nap_complete"
                self.state.awake_ticks = 0
                self.state.sleep_ticks = 0
                self.state.sleep_need = 0.0
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
