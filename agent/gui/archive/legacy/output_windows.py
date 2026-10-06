from __future__ import annotations
import json, re, subprocess, time
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QPixmap, QBrush
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
try:
    from PySide6.QtSvg import QSvgRenderer
except Exception:
    QSvgRenderer = None

ROOT=Path("/mnt/gai")
CTRL=ROOT/"state/output_windows.json"
PIDFILE=ROOT/"state/output_windows.pid"
SCREEN=ROOT/"state/viewfinder.png"
CREATIVE=ROOT/"creative"

def read_json(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

def latest(folder,suffix):
    try:
        xs=sorted(folder.rglob("*"+suffix),key=lambda p:p.stat().st_mtime,reverse=True)
        return xs[0] if xs else None
    except Exception: return None

class OutputWindow(QWidget):
    def __init__(self,title,kind,w=390,h=220):
        super().__init__(None, Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)
        self.kind=kind; self.title=title
        self.setAttribute(Qt.WA_TranslucentBackground,False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.resize(w,h)
        self.label=QLabel(self); self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.label.setStyleSheet("QLabel{background:rgb(8,13,20);color:#dce7f5;border:1px solid rgba(112,217,255,150);border-radius:18px;padding:12px;font-size:13px;}")
        self.label.setGeometry(0,0,w,h)
    def refresh(self, cfg):
        spec=cfg.get(self.kind,{})
        self.setVisible(bool(spec.get("visible",True)))
        self.setWindowOpacity(1.0)
        self.move(int(spec.get("x",40)),int(spec.get("y",40)))
        self.label.setStyleSheet("QLabel{background:rgb(8,13,20);color:#dce7f5;border:1px solid rgba(112,217,255,150);border-radius:18px;padding:12px;font-size:%dpx;}"%int(spec.get("font_size",13)))
        self.render()

    def render(self):
        if self.kind=="thought": self.render_thought()
        elif self.kind=="text": self.render_text()
        elif self.kind=="pixels": self.render_pixels()
        elif self.kind=="view": self.render_view()

    def render_thought(self):
        rows=[]
        for path in (ROOT/"state/autonomous_cognition.jsonl",ROOT/"state/thoughts.jsonl"):
            try:
                for line in path.read_text().splitlines()[-6:]:
                    d=json.loads(line); rows.append(d)
                if rows: break
            except Exception: pass
        if not rows: self.label.setText("THOUGHTS\n\nwaiting…"); return
        d=rows[-1]; text=" ".join(str(d.get("thought",d.get("text",""))).split())
        shown=int(time.time()*3)*3
        shown=min(len(text),shown)
        self.label.setText("THOUGHT STREAM • 3 LETTERS\n\n"+"▌ "+text[:shown])

    def render_text(self):
        p=latest(CREATIVE/"text",".txt")
        self.label.setText("TEXT OUTPUT • G.A.I.\n\n"+(p.read_text()[:850] if p else "waiting for a text artifact…"))

    def render_pixels(self):
        p=latest(CREATIVE/"paint",".svg") or latest(CREATIVE/"images",".svg")
        if not p:
            self.label.setText("PIXELS / DRAWING PAD • G.A.I.\n\nwaiting for an artwork artifact…"); return
        if QSvgRenderer:
            canvas=QImage(self.width()-24,self.height()-50,QImage.Format_ARGB32); canvas.fill(Qt.transparent)
            renderer=QSvgRenderer(str(p)); painter=QPainter(canvas); renderer.render(painter); painter.end()
            self.label.setText("PIXELS / DRAWING PAD • G.A.I.\n\n"+p.name)
            self.label.setPixmap(QPixmap.fromImage(canvas)); return
        self.label.setText("PIXELS / DRAWING PAD • G.A.I.\n\n"+p.name)

    def render_view(self):
        im=QImage(str(SCREEN))
        if im.isNull():
            self.label.setText("VIEW FINDER • G.A.I.\n\nno visual field yet"); return
        im=im.scaled(self.width()-24,self.height()-50,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        p=QPainter(im); g=read_json(ROOT/"state/gaze.json")
        x=max(0,min(1,float(g.get("x",.5)))); y=max(0,min(1,float(g.get("y",.5))))
        px=int(x*im.width()); py=int(y*im.height()); p.setPen(QPen(QColor(70,220,255,220),2))
        p.drawLine(px-10,py,px+10,py); p.drawLine(px,py-10,px,py+10); p.end()
        self.label.setText("VIEW FINDER • G.A.I. VISUAL FIELD")
        self.label.setPixmap(QPixmap.fromImage(im))

class InteractionOverlay(QWidget):
    """Click-through visual cue showing the body reaching for an active toy."""
    def __init__(self, screen):
        super().__init__(None, Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setGeometry(screen.geometry())
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(80)

    def paintEvent(self, event):
        interaction=read_json(ROOT/"state/toy_interaction.json")
        if not interaction.get("active"): return
        if time.time()-float(interaction.get("timestamp",0)) > 2.2: return
        cfg=read_json(CTRL)
        tool=interaction.get("tool","")
        spec=cfg.get(tool,{})
        if not spec.get("visible",True): return

        proprio=read_json(ROOT/"state/proprioception.json")
        bx=float(proprio.get("x",960))+float(proprio.get("width",90))/2
        by=float(proprio.get("y",540))+float(proprio.get("height",90))/2
        tx=float(spec.get("x",470))+({'view':215,'thought':195,'text':195,'pixels':195}.get(tool,195))
        ty=float(spec.get("y",25))+({'view':135,'thought':90,'text':110,'pixels':110}.get(tool,110))

        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen=QPen(QColor(112,217,255,205),3)
        p.setPen(pen)
        p.drawLine(QPointF(bx,by),QPointF(tx,ty))

        # Small animated "hand": palm + four fingers pointing at the toy.
        p.setBrush(QBrush(QColor(220,235,245,235)))
        p.setPen(QPen(QColor(8,13,20,230),2))
        p.drawEllipse(QRectF(tx-11,ty-9,22,18))
        p.drawLine(QPointF(tx-5,ty-8),QPointF(tx-8,ty-19))
        p.drawLine(QPointF(tx,ty-8),QPointF(tx,ty-22))
        p.drawLine(QPointF(tx+5,ty-7),QPointF(tx+8,ty-19))
        p.drawLine(QPointF(tx+10,ty-2),QPointF(tx+17,ty-9))
        p.end()


class Manager:
    def __init__(self):
        self.app=QApplication([])
        PIDFILE.parent.mkdir(parents=True, exist_ok=True)
        PIDFILE.write_text(str(__import__("os").getpid()))
        self.windows={
            "view":OutputWindow("view","view",430,270),
            "thought":OutputWindow("thought","thought",390,180),
            "text":OutputWindow("text","text",390,220),
            "pixels":OutputWindow("pixels","pixels",390,220)}
        self.overlay=InteractionOverlay(self.app.primaryScreen())
        self.overlay.show()
        self.defaults={
            "view":{"visible":True,"x":25,"y":25,"opacity":.72},
            "thought":{"visible":True,"x":470,"y":25,"opacity":.72},
            "text":{"visible":True,"x":470,"y":220,"opacity":.72},
            "pixels":{"visible":True,"x":470,"y":455,"opacity":.72}}
        self.timer=QTimer(); self.timer.timeout.connect(self.refresh); self.timer.start(350)
        self.refresh()
        for w in self.windows.values(): w.show()
        self.app.exec()

    def refresh(self):
        cfg=read_json(CTRL)
        merged={k:{**self.defaults[k],**cfg.get(k,{})} for k in self.windows}
        for k,w in self.windows.items(): w.refresh(merged)

if __name__=="__main__":
    Manager()
