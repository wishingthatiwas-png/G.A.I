from perception.senses import Senses

def test_senses():
    s = Senses()
    obs = s.observe()
    s.close()
    # The laptop organism currently has a screen-based visual organ rather than a webcam.
    # A physical camera is optional hardware, so absence must not make the sensory test fail.
    if obs['camera'] is not None:
        assert obs['camera']['width'] > 0
    assert obs['audio'] is not None


def test_habituation_builds_and_recovers(tmp_path, monkeypatch):
    monkeypatch.setattr(Senses, "HABITUATION_PATH", tmp_path / "habituation.json")
    s = Senses()
    first = s._apply_habituation("same-stimulus")
    second = s._apply_habituation("same-stimulus")
    novel = s._apply_habituation("new-stimulus")
    assert second > first
    assert novel < second
