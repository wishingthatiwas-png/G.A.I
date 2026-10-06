from types import SimpleNamespace

from core.wants import WantSystem
from core.motivation import MotivationSystem
from core.homeostasis import CoreNeeds


def test_wants_are_desired_outcomes_not_commands():
    needs = SimpleNamespace(rest=0.1, sleep_need=0.0, social=0.0, processing=0.2,
                            storage_pressure=0.0, memory_pressure=0.0, energy=0.8)
    state = SimpleNamespace(boredom=0.9)
    perception = {"senses": {"vision": {"sensory_novelty": 0.8, "patterns": []},
                             "audio": {"auditory": {"rms": 0.0}}}}
    system = WantSystem()
    wants = system.derive(needs, state=state, perception=perception)
    assert wants
    assert wants[0].name == "explore_novelty"
    assert all(not hasattr(w, "command") for w in wants)


def test_wants_change_with_context():
    needs = SimpleNamespace(rest=0.0, sleep_need=0.0, social=0.0, processing=0.2,
                            storage_pressure=0.0, memory_pressure=0.0, energy=0.9)
    state = SimpleNamespace(boredom=0.0)
    system = WantSystem()
    visual = {"senses": {"vision": {"sensory_novelty": 0.8}, "audio": {"auditory": {"rms": 0.0}}}}
    quiet = {"senses": {"vision": {"sensory_novelty": 0.0}, "audio": {"auditory": {"rms": 0.0}}}}
    assert system.derive(needs, state=state, perception=visual)[0].name == "explore_novelty"
    assert system.derive(needs, state=state, perception=quiet)[0].name != "explore_novelty"


def test_motivation_scores_include_wants_without_executing_them():
    needs = CoreNeeds(power=0.7, social=0.0, temperature=0.0, processing=0.2,
                      energy=0.8, rest=0.1, sleep_need=0.0, storage_pressure=0.0,
                      memory_pressure=0.0, storage_sleep_need=0.0)
    perception = {"system": {"load_1m": 0.2, "memory_percent": 20, "cpu_count": 4},
                  "senses": {"vision": {"sensory_novelty": 0.9}, "audio": {}}}
    state = SimpleNamespace(boredom=0.8)
    m = MotivationSystem()
    m.bind_state(state)
    m.update(needs, perception)
    assert m.wants.strongest()["name"] == "explore_novelty"
    assert m.score_action("explore") > m.score_action("rest")
    assert m.wants.strongest()["action_affinity"] == "explore"
