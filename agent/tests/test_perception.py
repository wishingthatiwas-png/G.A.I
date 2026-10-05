from perception.system import snapshot as system_snapshot
from perception.hardware import snapshot as hardware_snapshot

def test_system():
    s = system_snapshot()
    assert s['memory_total'] > 0
    assert s['cpu_count'] >= 1

def test_hardware():
    h = hardware_snapshot()
    assert isinstance(h['camera_devices'], list)
