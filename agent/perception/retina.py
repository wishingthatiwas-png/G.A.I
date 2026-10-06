from __future__ import annotations

import time
import numpy as np


class ReactiveRetina:
    """Cheap bottom-up retinal reflex layer.

    It compares downsampled luminance frames, detects sudden/large change and
    emits an orienting target before expensive vision/CC processing.
    """

    def __init__(self, width=96, height=54):
        self.width = int(width)
        self.height = int(height)
        self.previous = None
        self.last_event = None

    def _small_gray(self, frame):
        if frame is None:
            return None
        arr = np.asarray(frame)
        if arr.ndim == 3:
            arr = arr.mean(axis=2)
        h, w = arr.shape[:2]
        ys = np.linspace(0, h - 1, self.height).astype(int)
        xs = np.linspace(0, w - 1, self.width).astype(int)
        return arr[np.ix_(ys, xs)].astype(np.float32)

    def inspect(self, frame):
        gray = self._small_gray(frame)
        if gray is None:
            return {"changed": False, "large_change": False, "strength": 0.0, "reason": "no_frame"}

        if self.previous is None:
            self.previous = gray
            return {"changed": False, "large_change": False, "strength": 0.0, "reason": "baseline"}

        diff = np.abs(gray - self.previous)
        moving = diff > 20.0
        ratio = float(np.mean(moving))
        strength = float(min(1.0, np.mean(diff) / 255.0 * 10.0))
        large = ratio >= 0.12 or strength >= 0.22

        if np.any(moving):
            ys, xs = np.nonzero(moving)
            x = float(np.mean(xs) / max(1, self.width - 1))
            y = float(np.mean(ys) / max(1, self.height - 1))
        else:
            x, y = 0.5, 0.5

        self.previous = gray
        event = {
            "timestamp": time.time(),
            "changed": bool(ratio >= 0.015 or strength >= 0.06),
            "large_change": bool(large),
            "strength": round(strength, 4),
            "change_ratio": round(ratio, 4),
            "x": round(x, 3),
            "y": round(y, 3),
            "reason": "large_movement" if large else ("movement" if ratio >= 0.015 else "stable"),
            "reflex": "orient" if large else ("track" if ratio >= 0.015 else "none"),
        }
        self.last_event = event
        return event
