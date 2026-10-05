from perception.senses import Senses

def test_senses():
    s = Senses()
    obs = s.observe()
    s.close()
    assert obs['camera'] is not None
    assert obs['camera']['width'] > 0
    assert obs['audio'] is not None
