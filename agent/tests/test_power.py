from core.homeostasis import CoreNeeds
from core.motivation import EmotionState, InstinctState
from core.power import PerformanceGovernor


def test_high_stress_is_performance_when_body_is_healthy():
    governor = PerformanceGovernor()
    needs = CoreNeeds(power=1.0, temperature=0.1)
    emotions = EmotionState(fear=0.95, anxiety=0.95, frustration=0.9, fatigue=0.2)
    instincts = InstinctState(threat=0.95)
    assert governor.choose(1.0, False, needs, emotions, instincts) == "performance"


def test_critical_heat_overrides_stress():
    governor = PerformanceGovernor()
    needs = CoreNeeds(power=1.0, temperature=0.95)
    emotions = EmotionState(fear=1.0, anxiety=1.0, fatigue=0.1)
    assert governor.choose(1.0, False, needs, emotions, InstinctState(threat=1.0)) == "power-saver"


def test_critical_battery_overrides_stress():
    governor = PerformanceGovernor()
    needs = CoreNeeds(power=0.05, temperature=0.1)
    emotions = EmotionState(fear=1.0, anxiety=1.0, fatigue=0.1)
    assert governor.choose(0.05, False, needs, emotions, InstinctState(threat=1.0)) == "power-saver"


def test_exhaustion_downshifts():
    governor = PerformanceGovernor()
    needs = CoreNeeds(power=1.0, temperature=0.1)
    emotions = EmotionState(fear=0.9, fatigue=0.98)
    assert governor.choose(1.0, False, needs, emotions, InstinctState(threat=0.9)) == "balanced"


def test_snapshot_exposes_current_profile():
    governor = PerformanceGovernor()
    assert governor.snapshot() == {"profile": None}
    governor.profile = "performance"
    assert governor.snapshot() == {"profile": "performance"}
