from hardware.simulated_hdd_organ import SimulatedHDDOrgan
from core.deep_archive import DeepArchive
from core.deep_storage import MemoryBank


def test_simulated_hdd_lifecycle(tmp_path):
    organ = SimulatedHDDOrgan(tmp_path / "hdd", tmp_path / "state.json")
    assert organ.attach()["attached"]
    assert organ.verify()
    organ.begin_write()
    organ.end_write()
    organ.simulate_failure()
    assert not organ.state.present
    organ.restore()
    assert organ.state.present


def test_compressed_deep_memory_round_trip(tmp_path):
    root = tmp_path / "deep"
    archive = DeepArchive(root)
    archive.attach("test-organ", str(root))
    manifest = root / "manifest.json"
    manifest.write_text('{"format":"gai-deep-memory","archive_id":"test-organ"}')
    assert archive.verify_manifest(manifest)
    archive.set_phase("dream")
    archive.begin_dream_write()
    archive.commit_memory("mem-test", {"words": ["round", "trip"], "value": 42})
    archive.end_dream_write()
    bank = MemoryBank(root)
    bank_id = "bank-" + __import__("time").strftime("%Y%m%d")
    result = bank.validate(bank_id)
    assert result["ok"]
    assert bank.read(bank_id)[0]["memory_id"] == "mem-test"
