from __future__ import annotations
from pathlib import Path
import time
import cv2

class Camera:
    def __init__(self, device=0, width=1280, height=720, fps=30):
        self.device = device
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.output = Path('/mnt/gai/data/observations/camera')
        self.output.mkdir(parents=True, exist_ok=True)

    def read(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def capture(self):
        frame = self.read()
        if frame is None:
            return None
        path = self.output / f'{time.time_ns()}.jpg'
        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        return {'path': str(path), 'width': int(frame.shape[1]), 'height': int(frame.shape[0])}

    def close(self):
        self.cap.release()
