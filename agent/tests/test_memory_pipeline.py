import json
from core.memory_pipeline import Experience, MemoryPipeline

def test_ingest_and_select(tmp_path):
    p=MemoryPipeline(tmp_path)
    e=Experience('observation',{'words':['red door'],'shapes':['rectangle']},novelty=.9,emotional_intensity=.8)
    assert p.ingest(e)>.45
    assert p.select_for_sleep()

def test_symbolic_encoding(tmp_path):
    p=MemoryPipeline(tmp_path)
    e=Experience('scene',{'words':['corridor'],'shapes':['rectangle'],'relations':['person-left-of-door'],'emotion':{'fear':.6}},importance=.8)
    s=p.symbolic_encode(e)
    assert s['type']=='symbolic_reconstruction' and s['relations']==['person-left-of-door']


def test_reinforce_and_decay(tmp_path):
    p=MemoryPipeline(tmp_path)
    e=Experience('x',{'words':['test']},novelty=.5,importance=.5)
    p.ingest(e); assert p.reinforce(e.memory_id)
    before=json.loads(p.queue.read_text())['importance']
    p.decay(); after=json.loads(p.queue.read_text())['importance']
    assert after < before


def test_retrieve_by_symbolic_overlap(tmp_path):
    p=MemoryPipeline(tmp_path)
    p.ingest(Experience('scene',{'words':['red','door']},novelty=.9,importance=.8))
    p.ingest(Experience('scene',{'words':['blue','car']},novelty=.2,importance=.2))
    r=p.retrieve(['red'],limit=1)
    assert r and r[0]['kind']=='scene'


def test_reconstruction_prompt(tmp_path):
    p=MemoryPipeline(tmp_path)
    e=Experience('scene',{'words':['red door'],'shapes':['rectangle'],'relations':['person-left-of-door']})
    prompt=p.create_reconstruction_prompt(p.symbolic_encode(e))
    assert 'red door' in prompt and 'person-left-of-door' in prompt
