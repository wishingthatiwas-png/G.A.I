from __future__ import annotations
import numpy as np

class TemporalVision:
    def __init__(self):
        self.previous = None

    def compare(self, frame):
        if frame is None:
            return {'motion': 0.0, 'changed': False}
        gray = frame if len(frame.shape)==2 else frame.mean(axis=2)
        gray = gray.astype(np.float32)
        if self.previous is None:
            self.previous = gray
            return {'motion': 0.0, 'changed': False}
        diff = np.abs(gray - self.previous)
        motion = float(np.mean(diff) / 255.0)
        self.previous = gray
        return {'motion': motion, 'changed': motion > 0.015}
