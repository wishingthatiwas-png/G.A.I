from __future__ import annotations
from .camera import Camera
from .audio import sample
from .vision import analyse, spatial_summary

class Senses:
    def __init__(self):
        self.camera = Camera()

    def observe(self):
        cam = self.camera.capture()
        audio = None
        try:
            audio = sample()
        except Exception as e:
            audio = {'error': type(e).__name__}
        vision = None
        if cam:
            import cv2
            frame = cv2.imread(cam['path'])
            vision = analyse(frame)
            vision['objects'] = spatial_summary(vision['objects'])
        return {'camera': cam, 'audio': audio, 'vision': vision}

    def close(self):
        self.camera.close()
