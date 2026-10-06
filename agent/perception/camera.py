from __future__ import annotations
from pathlib import Path
import threading, time
import cv2

class Camera:
    """Persistent visual stream. The brain consumes the latest frame; no frame archive is created."""
    def __init__(self, device=0, width=640, height=360, fps=15):
        self.device=device; self.width=width; self.height=height; self.fps=fps
        self.output=Path('/mnt/gai/state/camera_stream.jpg'); self.output.parent.mkdir(parents=True,exist_ok=True)
        self.cap=None; self.active=False; self.capture_count=0
        self._latest=None; self._latest_ts=0.0; self._lock=threading.Lock(); self._cap_lock=threading.Lock(); self._thread=None; self._stop=threading.Event()
        self.open()

    def open(self):
        if self.active and self.cap is not None and self.cap.isOpened(): return True
        cap=cv2.VideoCapture(self.device,cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,self.width); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,self.height); cap.set(cv2.CAP_PROP_FPS,self.fps)
        if not cap.isOpened():
            cap.release(); self.cap=None; self.active=False; return False
        self.cap=cap; self.active=True; self._stop.clear()
        if self._thread is None or not self._thread.is_alive():
            self._thread=threading.Thread(target=self._stream_loop,name='gai-camera-stream',daemon=True); self._thread.start()
        return True

    def _stream_loop(self):
        while not self._stop.is_set():
            cap=self.cap
            if cap is None or not cap.isOpened(): break
            with self._cap_lock:
                if self.cap is not cap or self._stop.is_set(): break
                ok,frame=cap.read()
            if not ok:
                time.sleep(.05); continue
            now=time.time()
            with self._lock:
                self._latest=frame
                self._latest_ts=now
                self.capture_count += 1
            if self.capture_count % max(1,int(self.fps)) == 0:
                try: cv2.imwrite(str(self.output),frame,[cv2.IMWRITE_JPEG_QUALITY,78])
                except Exception: pass

    def read(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def capture(self):
        frame=self.read()
        if frame is None: return None
        with self._lock: ts=self._latest_ts; count=self.capture_count
        return {'path':str(self.output),'width':int(frame.shape[1]),'height':int(frame.shape[0]),'timestamp':ts,'streaming':True,'frame_count':count,'_frame':frame}

    def close(self):
        self._stop.set()
        with self._cap_lock:
            cap=self.cap
            self.cap=None; self.active=False
            if cap is not None:
                try: cap.release()
                except Exception: pass
        self._thread=None
