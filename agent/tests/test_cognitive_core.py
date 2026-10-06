from core.nervous import NervousSystem
from cognition.core import CognitiveCore, GlobalWorkspace, Intention


def test_workspace_routes_processed_input():
    w = GlobalWorkspace()
    w.ingest("perception.observation", {"object": "cup"}, source="vision", novelty=.8)
    w.ingest("drive.update", {"name": "curiosity", "value": .7}, source="drive")
    w.ingest("prediction.error", {"error": .2}, source="prediction")
    assert w.current_experience[-1]["payload"]["object"] == "cup"
    assert w.concerns[-1]["payload"]["name"] == "curiosity"
    assert w.predictions[-1]["payload"]["error"] == .2


def test_intention_validation_rejects_unknown_action():
    assert Intention("explode_hardware", priority=9).validate().type == "none"
    assert Intention("observe", priority=9).validate().priority == 1.0
    assert Intention("vocalize", priority=.8).validate().type == "vocalize"


def test_cognitive_core_produces_structured_output_and_publishes():
    n = NervousSystem()
    seen = []
    n.subscribe("cognition.*", lambda e: seen.append(e), name="test-cognition")

    def model(prompt):
        assert prompt["protocol"] == "G.A.I.-CC-V1"
        assert prompt["workspace"]["current_experience"]
        return {"thought":"I notice a new observation.",
                "intention":{"type":"investigate","target":"cup","priority":.7,"reason":"clarify novelty"},
                "prediction":"The next observation may clarify it.","confidence":.81}

    core = CognitiveCore(nervous=n, model=model, state_path="/tmp/gai-cc-test.jsonl")
    n.publish("perception.observation", {"object":"cup"}, source="vision", novelty=.9)
    n.dispatch()
    out = core.think()
    n.dispatch()
    assert out.thought == "I notice a new observation."
    assert out.intention.type == "investigate"
    assert out.confidence == .81
    assert any(e.kind == "cognition.intention" for e in seen)


def test_model_failure_is_safe():
    core = CognitiveCore(model=lambda _: 1/0, state_path="/tmp/gai-cc-test-error.jsonl")
    out = core.think()
    assert out.intention.type == "none"
    assert out.confidence == 0.0
    assert core.last_error
