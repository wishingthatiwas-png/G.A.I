import numpy as np
from perception.vision import analyse, spatial_summary

def test_vision_basic():
    img=np.zeros((200,300,3), dtype=np.uint8)
    img[40:140,80:220]=(0,0,255)
    v=analyse(img)
    assert v['image']['width']==300
    assert isinstance(v['objects'], list)
    assert isinstance(spatial_summary(v['objects']), list)
