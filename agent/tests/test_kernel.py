import json
from pathlib import Path
from core.kernel import Kernel

def test_kernel_cycle():
    k = Kernel()
    s = k.tick()
    assert s['world']['observation_count'] >= 1
    assert s['action']['type'] in {'rest','maintain','interact','explore'}
    assert Path('/mnt/gai/state/runtime.json').exists()

def test_memory():
    k = Kernel()
    before = k.memory.db.execute('select count(*) from events').fetchone()[0]
    k.tick()
    after = k.memory.db.execute('select count(*) from events').fetchone()[0]
    assert after > before
