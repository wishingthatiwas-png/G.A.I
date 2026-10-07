from __future__ import annotations
from pathlib import Path
import threading, time, json
import cv2

class Camera:
    """Persistent visual stream. The brain consumes the latest frame; no frame archive is created."""
    def __init__(self, device=0, width=640, height=360, fps=15):
        self.device=device; self.width=width; self.height=height; self.fps=fps
        self.output=Path('/mnt/gai/state/camera_stream.jpg'); self.output.parent.mkdir(parents=True,exist_ok=True)
        self.status_path=Path('/mnt/gai/state/camera_organ.json')
        self.cap=None; self.active=False; self.capture_count=0
        self._latest=None; self._latest_ts=0.0; self._lock=threading.Lock(); self._cap_lock=threading.Lock(); self._thread=None; self._stop=threading.Event()
        self.open()

    def open(self):
        if self.active and self.cap is not None and self.cap.isOpened():
            if self._thread is None or not self._thread.is_alive():
                self._stop.clear()
                self._thread=threading.Thread(target=self._stream_loop,name='gai-camera-stream',daemon=True)
                self._thread.start()
            return True
        cap=cv2.VideoCapture(self.device,cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,self.width); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,self.height); cap.set(cv2.CAP_PROP_FPS,self.fps)
        if not cap.isOpened():
            cap.release(); self.cap=None; self.active=False
            try: self.status_path.write_text(json.dumps({'available':False,'streaming':False,'device':self.device,'timestamp':time.time(),'error':'open_failed'},separators=(',',':')))
            except Exception: pass
            return False
        self.cap=cap; self.active=True; self._stop.clear()
        try: self.status_path.write_text(json.dumps({'available':True,'streaming':True,'device':self.device,'width':self.width,'height':self.height,'fps':self.fps,'timestamp':time.time()},separators=(',',':')))
        except Exception: pass
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
                try:
                    ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 78])
                    if ok:
                        tmp = self.output.with_suffix('.jpg.tmp')
                        tmp.write_bytes(encoded.tobytes())
                        tmp.replace(self.output)
                except Exception:
                    pass
                try:
                    self.status_path.write_text(json.dumps({
                        'available': True, 'streaming': True, 'device': self.device,
                        'width': self.width, 'height': self.height, 'fps': self.fps,
                        'frame_count': self.capture_count, 'last_frame': now,
                        'timestamp': now, 'output': str(self.output),
                    }, separators=(',', ':')))
                except Exception:
                    pass

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
        # The capture loop is a native OpenCV boundary. Do not leave it alive
        # for interpreter teardown: wait for the worker to observe the stop
        # signal and finish before dropping the thread reference.
        thread=self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        self._thread=None
