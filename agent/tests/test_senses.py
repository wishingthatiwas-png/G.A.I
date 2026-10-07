from perception.senses import Senses

def test_senses():
    s = Senses()
    obs = s.observe()
    s.close()
    assert obs['camera']['available'] is False
    assert obs['camera']['disabled'] is True
    assert obs['visual_stream']['mode'] == 'in'
    assert obs['visual_stream']['path'].endswith('/state/screen_stream.jpg')
    assert obs['audio'] is not None


def test_habituation_builds_and_recovers(tmp_path, monkeypatch):
    monkeypatch.setattr(Senses, "HABITUATION_PATH", tmp_path / "habituation.json")
    s = Senses()
    try:
        first = s._apply_habituation("same-stimulus")
        second = s._apply_habituation("same-stimulus")
        novel = s._apply_habituation("new-stimulus")
        assert second > first
        assert novel < second
    finally:
        s.close()
