from __future__ import annotations
from .camera import Camera
from .audio import sample

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
        return {'camera': cam, 'audio': audio}

    def close(self):
        self.camera.close()
