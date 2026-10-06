from __future__ import annotations
import json, math, os, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'
FOCUS=STATE/'sight_focus.json'; PROPRIO=STATE/'proprioception.json'; INFO=STATE/'focus_bubble.json'; PID=STATE/'focus_bubble.pid'

def read(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

class FocusBubble(QWidget):
    """Invisible gaze target. CNS moves it; the phenotype eye follows its state."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint|Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground,True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.setAttribute(Qt.WA_ShowWithoutActivating,True)
        self.resize(2,2)
        self._last=None
        PID.write_text(str(os.getpid()))
        self.refresh()

    def refresh(self):
        f=read(FOCUS); prop=read(PROPRIO); screen=QApplication.primaryScreen()
        if screen is None: return
        geom=screen.availableGeometry()
        mode='out' if str(f.get('mode','in'))=='out' else 'in'
        if mode!='in':
            self.hide()
            INFO.write_text(json.dumps({'visible':False,'mode':mode,'timestamp':time.time()},separators=(',',':')))
            return
        x=max(0,min(1,float(f.get('x',.5)))); y=max(0,min(1,float(f.get('y',.78))))
        px=int(geom.left()+x*geom.width())-1; py=int(geom.top()+y*geom.height())-1
        self.move(px,py); self.show()
        bx=float(prop.get('x',geom.center().x())); by=float(prop.get('y',geom.center().y()))
        bw=float(prop.get('width',270)); bh=float(prop.get('height',270))
        bc=(bx+bw/2,by+bh/2); fc=(px+1,py+1)
        dist=math.hypot(fc[0]-bc[0],fc[1]-bc[1])
        INFO.write_text(json.dumps({
            'visible':True,'mode':'in','x':x,'y':y,'screen_x':fc[0],'screen_y':fc[1],
            'distance_px':round(dist,1),'timestamp':time.time(),
            'target':f.get('target'),'reason':f.get('reason')
        },separators=(',',':')))

    def closeEvent(self,event):
        try: PID.unlink()
        except FileNotFoundError: pass
        super().closeEvent(event)

def main():
    app=QApplication([]); w=FocusBubble()
    timer=QTimer(w); timer.timeout.connect(w.refresh); timer.start(80)
    return app.exec()

if __name__=='__main__':
    raise SystemExit(main())
