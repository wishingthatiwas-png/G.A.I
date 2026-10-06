from core.sensory import SensoryDock

def test_detachable_organs():
    d = SensoryDock()
    d.detach("vision.local")
    assert not d.snapshot()["organs"]["vision.local"]["connected"]
    d.attach("vision.local", "vision", ["camera"])
    assert d.snapshot()["organs"]["vision.local"]["connected"]

def test_sleep_gating():
    d = SensoryDock()
    d.set_phase("pre_sleep", 0.85)
    assert d.snapshot()["organs"]["hearing.local"]["sensitivity"] < 1
    d.set_phase("dream", 0.9)
    assert not d.snapshot()["organs"]["hearing.local"]["enabled"]
    assert d.should_wake("hearing.local", 1.1)

def test_fatigue_changes_threshold():
    d = SensoryDock()
    d.set_phase("awake", 0.1)
    rested = d.snapshot()["organs"]["hearing.local"]["wake_threshold"]
    d.set_phase("awake", 0.9)
    tired = d.snapshot()["organs"]["hearing.local"]["wake_threshold"]
    assert tired > rested
