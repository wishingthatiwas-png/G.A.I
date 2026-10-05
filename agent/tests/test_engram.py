from memory.engram import AssociativeMemory

def test_association_strengthens(tmp_path, monkeypatch):
    import memory.engram as em
    monkeypatch.setattr(em, 'MEMORY_DIR', tmp_path)
    m=AssociativeMemory()
    a=m.fire(['red','sound'], {'curiosity':.8,'stress':.2}, reward=.5)
    b=m.fire(['red','sound'], {'curiosity':.8,'stress':.2}, reward=.5)
    assert b.associations[0]['weight'] > a.associations[0]['weight']
