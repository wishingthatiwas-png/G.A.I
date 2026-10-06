from __future__ import annotations
import json, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'
FOCUS=STATE/'sight_focus.json'; SCREEN=STATE/'screen_stream.jpg'; CAMERA=STATE/'camera_stream.jpg'

def read(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

class Viewfinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('G.A.I. Viewfinder')
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint|Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating,True)
        self.resize(210,150); self.move(350,70)
        self._focus={}; self._frame=None; self._last_stamp=0

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.SmoothPixmapTransform,False)
        w,h=self.width(),self.height()
        p.fillRect(0,0,w,h,QColor(7,8,7,245))
        if self._frame and not self._frame.isNull():
            pix=self._frame.scaled(w-14,h-34,Qt.KeepAspectRatio,Qt.FastTransformation)
            x=(w-pix.width())//2; y=8+(h-34-pix.height())//2
            p.drawPixmap(x,y,pix)
        # retro glass / scanlines
        p.setPen(QPen(QColor(180,210,170,24),1))
        for y in range(8,h-25,4): p.drawLine(7,y,w-8,y)
        f=self._focus; mode=f.get('mode','out')
        if mode=='in':
            x=7+int(float(f.get('x',.5))*(w-14)); y=8+int(float(f.get('y',.5))*(h-34))
            r=max(7,int(float(f.get('radius',.18))*min(w,h)*.45))
            pen=QPen(QColor(190,235,180,210),1.2); p.setPen(pen)
            p.drawRect(x-r,y-r,x+r,y+r); p.drawLine(x-7,y,x+7,y); p.drawLine(x,y-7,x,y+7)
            label='IN / SCREEN'
        else:
            p.setPen(QPen(QColor(190,235,180,170),1)); p.drawEllipse(w//2-12,h//2-12,w//2+12,h//2+12)
            p.drawLine(w//2-18,h//2,w//2+18,h//2); p.drawLine(w//2,h//2-18,w//2,h//2+18)
            label='OUT / CAMERA'
        p.setPen(QPen(QColor(190,235,180,190),1)); p.drawRect(2,2,w-5,h-27)
        p.setPen(QColor(205,230,195,190)); p.setFont(p.font()); p.drawText(8,h-10,label)
        p.end()

    def refresh(self):
        self._focus=read(FOCUS)
        mode=self._focus.get('mode','out')
        path=CAMERA if mode=='out' else SCREEN
        try:
            img=QPixmap(str(path))
            if not img.isNull(): self._frame=img
        except Exception: pass
        self.update()

def main():
    app=QApplication([])
    w=Viewfinder(); w.show(); w.raise_()
    t=QTimer(w); t.timeout.connect(lambda:(w.refresh(),w.raise_())); t.start(180)
    return app.exec()

if __name__=='__main__': raise SystemExit(main())
