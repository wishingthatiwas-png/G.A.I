import json
import pytest
from pathlib import Path
from core.kernel import Kernel

@pytest.fixture
def kernel():
    k = Kernel(acquire_lock=False)
    yield k
    k.close()

def test_kernel_cycle(kernel):
    k = kernel
    s = k.tick()
    assert s['world']['observation_count'] >= 1
    assert s['action']['type'] in {'rest','look','move','interact','vocalize','listen','wait'}
    assert Path('/mnt/gai/state/runtime.json').exists()

def test_memory(kernel):
    k = kernel
    before = k.memory.db.execute('select count(*) from events').fetchone()[0]
    k.tick()
    after = k.memory.db.execute('select count(*) from events').fetchone()[0]
    assert after >= before


def test_kernel_is_cell_driven(kernel):
    k = kernel
    s = k.tick()
    components = s["nervous"]["components"]
    for name in ("perception", "drives", "prediction", "control", "actions", "memory", "working_memory", "lifecycle", "supervisor"):
        assert components[name]["state"] == "running"
        assert components[name].get("error_count", 0) == 0
    assert s["nervous"]["metrics"]["errors"] == 0
    assert s["pipeline"]["correlation_id"]


def test_kernel_pipeline_is_correlated(kernel):
    k = kernel
    s = k.tick()
    correlation = s["pipeline"]["correlation_id"]
    trace = k.nervous.trace(correlation)
    kinds = {event["kind"] for event in trace}
    assert "perception.request" in kinds
    assert "perception.observation" in kinds
    assert "drive.update" in kinds
    assert "prediction.error" in kinds
    assert "cognition.thought" in kinds
    assert "cognition.intention" in kinds
    assert "action.completed" in kinds
    assert "memory.enqueued" in kinds
    assert "tick.completed" in kinds
