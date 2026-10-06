from core.homeostasis import CoreNeeds
from core.motivation import MotivationSystem
from cognition.v1 import BabyBrain


def test_phase2_needs_expose_distinct_pressures():
    needs = CoreNeeds(power=0.25, social=0.75, temperature=0.0, processing=0.4, energy=0.35, rest=0.7, sleep_need=0.6, storage_pressure=0.5)
    m = MotivationSystem()
    m.update(needs, {"system": {"cpu_count": 4, "load_1m": 1.0, "memory_percent": 40}}, reward=0.0)
    pressures = m.need_pressures()
    assert pressures["energy"] > 0.5
    assert pressures["rest"] > 0.5
    assert pressures["social"] > 0.5
    assert pressures["maintenance"] > 0.3
    assert 0.0 <= pressures["exploration"] <= 1.0


def test_phase2_rest_pressure_changes_action_score():
    class K: pass
    k = K()
    k.state = type("S", (), {"fatigue": 0.8, "stress": 0.1, "curiosity": 0.2, "boredom": 0.1})()
    k.core_needs = CoreNeeds(rest=0.9, energy=0.3, power=0.5)
    k.motivation = MotivationSystem()
    k.motivation.update(k.core_needs, {"system": {"cpu_count": 4, "load_1m": 0.2, "memory_percent": 20}}, reward=0.0)
    k.motivation.bind_state(k.state)
    k.motivation.remember_instinct(k.motivation.instincts.evaluate(k.core_needs, {"system": {"cpu_count": 4, "load_1m": 0.2, "memory_percent": 20}}))
    brain = BabyBrain.__new__(BabyBrain)
    brain.kernel = k
    assert k.motivation.score_action("rest") > k.motivation.score_action("explore")


def test_phase2_safety_can_veto():
    needs = CoreNeeds(power=0.5, temperature=1.0, processing=0.1)
    m = MotivationSystem()
    instinct = m.update(needs, {"system": {"cpu_count": 4, "load_1m": 0.1, "memory_percent": 20}}, reward=0.0)
    assert instinct.veto == "protect"
