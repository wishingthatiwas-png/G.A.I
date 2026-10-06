from pathlib import Path

from cognition.v1 import CNSState, V1World, BabyBrain, SharedAttention


class StubState:
    energy = 0.75
    curiosity = 0.7
    stress = 0.1
    satisfaction = 0.5
    boredom = 0.15
    fatigue = 0.1


class StubLearner:
    previous = None
    last_delta = {}

    def predict(self, action, context):
        return {}

    def choose(self, action, context, drives):
        self.previous = {"action": action}
        return {}


class StubKernel:
    state = StubState()
    learner = StubLearner()
    last_senses = {"vision": {"temporal": {"structure_change": 0.0}}}

    def current_context(self):
        return ["test"]

    def perception_novelty(self):
        return 0.0

    def drive_values(self):
        return {"curiosity": 0.7, "satisfaction": 0.5, "safety": 0.1, "energy": 0.25, "social": 0.0}


def test_world_interaction_produces_real_contact_and_reward(tmp_path):
    world = V1World(tmp_path / "world.json")
    result = world.interact(distance=40)
    assert result["reward"] == 1.0
    assert result["outcome"]["success"] is True
    skin = Path("/mnt/gai/state/digital_skin.json").read_text()
    assert '"contact":true' in skin
    assert world.observe()["state"] == "active"


def test_baby_brain_decides_without_language_model():
    brain = BabyBrain(StubKernel())
    decision = brain.decide()
    assert brain.cycle == 1
    assert decision["intention"]["type"] in {"rest", "look", "move", "interact", "vocalize", "wait"}
    assert decision["thought"]
    assert "prediction" in decision


def test_cns_reward_changes_affect_state():
    cns = CNSState()
    before = cns.satisfaction
    cns.apply_reward(1.0, 0.5)
    assert cns.satisfaction > before
    assert 0.0 <= cns.curiosity <= 1.0


def test_attention_prefers_audiovisual_event():
    attention = SharedAttention(Path("/tmp/gai-test-attention.json"))
    senses = {
        "vision": {
            "temporal": {"salience": 0.70, "onset": 0.40, "velocity": 0.20, "direction": "right"},
            "sensory_novelty": 0.80,
            "concepts": ["motion:present"],
            "patterns": [],
        },
        "audio": {
            "fresh": True,
            "signal": 0.50,
            "auditory": {"transient": 0.05},
        },
    }
    result = attention.select(senses, {"object": {"id": "curiosity_object", "state": "quiet"}}, {"curiosity": 0.7})
    assert result["selected"]["reason"] == "audiovisual_synchrony"


def test_experience_reward_belongs_to_current_action():
    class Policy:
        def __init__(self):
            self.calls = []

        def observe(self, action, context, reward):
            self.calls.append((action, reward))

    class Kernel(StubKernel):
        def __init__(self):
            self.state = StubState()
            self.learner = StubLearner()
            self.last_senses = {"vision": {"temporal": {"salience": 0.0}}}
            self.experience_policy = Policy()

    kernel = Kernel()
    brain = BabyBrain(kernel)
    brain.last_reward = -0.15
    brain.last_decision = {
        "intention": {"type": "move"},
        "thought": "move",
        "attention": {"selected": {"modality": "world", "target": "curiosity_object"}},
        "prediction": {},
        "experience_context": ["test"],
    }
    brain.record_outcome({"success": True})
    assert kernel.experience_policy.calls == [("move", 0.65)]


def test_old_interaction_reward_does_not_leak_into_move():
    brain = BabyBrain(StubKernel())
    brain.last_decision = {"intention": {"type": "move"}}
    brain.world.state["last_action"] = "interact"
    brain.world.state["last_reward"] = 1.0
    brain._observe_previous_outcome()
    assert brain.last_reward == 0.0
