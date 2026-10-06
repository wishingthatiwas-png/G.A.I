from pathlib import Path
import pytest
from core.deep_archive import DeepArchive, ArchiveError

def test_writes_only_during_dream(tmp_path):
    mount=tmp_path/"hdd"; mount.mkdir()
    a=DeepArchive(tmp_path/"archive")
    a.attach("TEST-HDD", str(mount))
    manifest=mount/"manifest.json"
    manifest.write_text('{"archive_id":"TEST-HDD","format":"gai-deep-memory"}')
    assert a.verify_manifest(manifest)
    with pytest.raises(ArchiveError): a.begin_dream_write()
    a.set_phase("dream")
    a.begin_dream_write()
    out=a.commit_memory("m1", {"scene":"red door", "shape":["door","person"]})
    assert out.exists()
    a.end_dream_write()
    with pytest.raises(ArchiveError): a.commit_memory("m2", {})

def test_detach_clears_access(tmp_path):
    a=DeepArchive(tmp_path/"archive")
    a.attach("X", "/mnt/example")
    a.detach()
    assert not a.snapshot()["attached"]
    assert not a.snapshot()["mounted"]
