from __future__ import annotations

import subprocess
import psutil

from .homeostasis import clamp


def level_and_charging():
    b = psutil.sensors_battery()
    if b is None:
        return 1.0, False
    return float(b.percent) / 100.0, bool(b.power_plugged)


class PerformanceGovernor:
    """Scale host performance from G.A.I.'s body state.

    This is deliberately coarse: Linux exposes performance tiers rather than a
    continuous performance dial through power-profiles-daemon.
    """

    def __init__(self):
        self.profile = None

    def choose(self, power, plugged, needs, emotions, instincts=None):
        power = clamp(power)
        thermal = clamp(getattr(needs, "temperature", 0.0))
        processing = clamp(getattr(needs, "processing", 0.0))
        fatigue = clamp(getattr(emotions, "fatigue", 0.0))
        stress = max(
            clamp(getattr(emotions, "fear", 0.0)),
            clamp(getattr(emotions, "anxiety", 0.0)),
            clamp(getattr(emotions, "frustration", 0.0)),
            clamp(getattr(getattr(emotions, "chemistry", None), "cortisol", 0.0)),
        )
        if instincts is not None:
            stress = max(stress, clamp(getattr(instincts, "threat", 0.0)))

        # Body protection always wins.
        if thermal >= 0.90 or power <= 0.12:
            return "power-saver"

        # Stress is mobilising: high stress increases performance demand rather
        # than reducing it. Only thermal danger, critical battery, or exhaustion
        # forces a protective downshift.
        if thermal >= 0.65 or fatigue >= 0.96:
            return "balanced"

        # Full/healthy power + arousal/stress = maximum performance.
        if power >= 0.90 and fatigue < 0.70:
            return "performance"

        # Plenty of power: stress/arousal can justify maximum performance.
        if power >= 0.60 and thermal < 0.55 and fatigue < 0.90:
            return "performance"

        return "balanced"

    def snapshot(self):
        return {"profile": self.profile}

    def apply(self, power, plugged, needs, emotions, instincts=None):
        target = self.choose(power, plugged, needs, emotions, instincts)
        if target == self.profile:
            return target

        try:
            result = subprocess.run(
                ["powerprofilesctl", "set", target],
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            )
            self.profile = target
        except Exception:
            # Never let performance management take down the cognitive kernel.
            return self.profile or "unknown"

        return self.profile
