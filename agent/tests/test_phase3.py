import tempfile
from pathlib import Path

from core.memory import Memory
from core.memory_pipeline import Experience, MemoryPipeline


def test_phase3_unified_recall_spans_tiers():
    with tempfile.TemporaryDirectory() as td:
        m = Memory(Path(td) / "events.db")
        m.store("short", "experience", {"words": ["curiosity_object"], "focus": "interact"}, key="s1", strength=0.6)
        m.store("long", "experience", {"words": ["curiosity_object", "active"], "focus": "interact"}, key="l1", strength=0.9)
        m.store("constant", "fact", {"words": ["curiosity_object"]}, key="c1", strength=1.0)
        hits = m.recall_relevant(["curiosity_object", "interact"], limit=10)
        assert {h["tier"] for h in hits} == {"short", "long", "constant"}
        assert hits[0]["relevance"] > 0


def test_phase3_recall_reinforces_memory():
    with tempfile.TemporaryDirectory() as td:
        m = Memory(Path(td) / "events.db")
        m.store("long", "experience", {"words": ["paint_pad"], "focus": "interact"}, key="paint", strength=0.6)
        before = m.recall_relevant(["paint_pad"], limit=1)[0]
        after = m.reinforce_relevant(["paint_pad"], limit=1, boost=0.1)[0]
        assert after["visits"] == before["visits"] + 1
        assert after["strength"] > before["strength"]


def test_phase3_pipeline_and_sql_memory_share_experience_id():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pipeline = MemoryPipeline(root / "pipeline")
        e = Experience("tick", {"words": ["curiosity_object"], "focus": "interact"}, novelty=0.8, reward=0.7)
        pipeline.ingest(e)
        assert any(row["memory_id"] == e.memory_id for row in pipeline._index_cache)
