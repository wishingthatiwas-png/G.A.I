import numpy as np
from perception.vision import TemporalVision, concepts

def test_temporal():
    t=TemporalVision()
    a=np.zeros((20,20),dtype=np.uint8)
    b=a.copy(); b[5:15,5:15]=255
    assert t.compare(a)['changed'] is False
    assert t.compare(b)['changed'] is True


def test_temporal_motion_direction_and_salience():
    t = TemporalVision()
    a = np.zeros((40, 40), dtype=np.uint8)
    b = a.copy(); b[10:20, 10:20] = 255
    c = a.copy(); c[10:20, 20:30] = 255
    t.compare(a)
    first = t.compare(b)
    second = t.compare(c)
    assert first['salience'] > 0.0
    assert second['velocity'] > 0.0
    assert second['direction'] == 'right'

def test_concepts():
    v={'objects':[{'colour':'red','shape':'circle','size':'small','position':'middle-center'}]}
    c=concepts(v, {'changed':True,'motion':.1})
    assert 'colour:red' in c
    assert 'motion:present' in c
