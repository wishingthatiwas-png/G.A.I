from pathlib import Path

from core.storage_backend import LocalSSDBackend
from core.memory_pipeline import Experience, MemoryPipeline
from core.learning import ExperiencePolicy


def test_v1_memory_backend_is_local_ssd_and_future_backends_are_inactive(tmp_path):
    backend = LocalSSDBackend(tmp_path / "memory")
    assert backend.name == "ssd"
    manifest = backend.manifest()
    assert manifest["backend"] == "ssd"
    assert "hdd" in manifest["expansion"]
    assert "cloud" in manifest["expansion"]


def test_memory_bank_round_trip_and_checksum(tmp_path):
    backend = LocalSSDBackend(tmp_path / "memory")
    payload = {"words": ["orb"], "objects": ["curiosity_object"], "reward": 0.7}
    path = backend.write("mem-test", payload)
    assert Path(path).exists()
    assert backend.read("mem-test") == payload

    Path(path).write_text(Path(path).read_text().replace('"orb"', '"tampered"'))
    assert backend.read("mem-test") is None


def test_memory_pipeline_uses_storage_backend(tmp_path):
    backend = LocalSSDBackend(tmp_path / "memory")
    pipeline = MemoryPipeline(tmp_path / "pipeline", backend=backend)
    experience = Experience(
        kind="closed_loop",
        content={"words": ["light"], "objects": ["light_switch"]},
        novelty=0.8,
        importance=1.0,
        reward=1.0,
    )
    pipeline.ingest(experience)
    committed = pipeline.consolidate(lambda mid, symbolic: backend.write(mid, symbolic))
    assert committed
    assert backend.exists(experience.memory_id)
    assert backend.read(experience.memory_id)["memory_id"] == experience.memory_id


def test_reward_changes_future_action_preference():
    policy = ExperiencePolicy(learning_rate=0.5, decay=0.0)
    context = ["vision", "curiosity_object"]
    before = policy.values(["interact", "rest"], context)
    policy.observe("interact", context, 0.9)
    after = policy.values(["interact", "rest"], context)
    assert after["interact"] > before["interact"]


def test_consequence_can_reduce_future_preference():
    policy = ExperiencePolicy(learning_rate=0.5, decay=0.0)
    context = ["audio", "failed_output"]
    policy.observe("vocalize", context, -0.9)
    assert policy.values(["vocalize"], context)["vocalize"] < 0.0
