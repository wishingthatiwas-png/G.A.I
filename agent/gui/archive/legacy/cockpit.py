from __future__ import annotations
import json, re, subprocess, time
from pathlib import Path
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame

ROOT=Path("/mnt/gai")
THOUGHTS=ROOT/"state/thoughts.jsonl"
RUNTIME=ROOT/"state/runtime.json"
MOTOR=ROOT/"state/motor_output.json"
CREATIVE=ROOT/"creative"
SCREEN=ROOT/"state/viewfinder.png"
PIXELS=ROOT/"state/pixel_output.json"

def read_json(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

def latest_thoughts(n=8):
    rows=[]
    # Prefer actual language-cognition cycles; fall back to the organism's
    # low-level presence stream when the model is quiet.
    for path in (ROOT/"state/autonomous_cognition.jsonl", THOUGHTS):
        try:
            for line in path.read_text().splitlines()[-n:]:
                try:
                    d=json.loads(line)
                    if path.name == "autonomous_cognition.jsonl":
                        d={"timestamp":d.get("timestamp"),"thought":d.get("thought",""),"action":d.get("action","")}
                    rows.append(d)
                except Exception: pass
            if rows: break
        except Exception: pass
    return rows[-n:]

def latest_file(folder, suffix):
    try:
        xs=sorted(folder.rglob("*"+suffix), key=lambda p:p.stat().st_mtime, reverse=True)
        return xs[0] if xs else None
    except Exception: return None

class Panel(QFrame):
    def __init__(self,title):
        super().__init__()
        self.setObjectName("panel")
        self.title=QLabel(title)
        self.title.setObjectName("title")
        self.body=QLabel()
        self.body.setWordWrap(True)
        self.body.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        lay=QVBoxLayout(self); lay.setContentsMargins(10,8,10,8); lay.setSpacing(5)
        lay.addWidget(self.title); lay.addWidget(self.body,1)

class Viewfinder(Panel):
    def __init__(self):
        super().__init__("VIEW FINDER • G.A.I. VISUAL FIELD")
        self.image=QLabel()
        self.image.setMinimumSize(360,210)
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet("background:#05070b;border-radius:8px;")
        self.layout().addWidget(self.image,1)
    def refresh(self):
        try:
            im=QImage(str(SCREEN))
            if not im.isNull():
                pix=im.scaled(self.image.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
                # Crosshair shows the current gaze point. Default is the screen centre.
                p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
                gaze=read_json(ROOT/"state/gaze.json")
                x=float(gaze.get("x",0.5)); y=float(gaze.get("y",0.5))
                px=int(max(0,min(1,x))*pix.width()); py=int(max(0,min(1,y))*pix.height())
                pen=QPen(QColor(70,220,255,210),2); p.setPen(pen)
                p.drawLine(px-12,py,px+12,py); p.drawLine(px,py-12,px,py+12)
                p.end()
                self.image.setPixmap(pix)
        except Exception: pass

class ThoughtPanel(Panel):
    def __init__(self):
        super().__init__("THOUGHT STREAM • 3 LETTERS")
        self.full=""; self.shown=0; self.last_id=None
        self.body.setStyleSheet("font-family:monospace;font-size:18px;")
    def refresh(self):
        rows=latest_thoughts(8)
        if not rows: return
        last=rows[-1]
        tid=last.get("timestamp", last.get("thought",""))
        if tid!=self.last_id:
            self.last_id=tid; self.full=" ".join(str(last.get("thought","")).split()); self.shown=0
        if self.shown < len(self.full):
            self.shown=min(len(self.full),self.shown+3)
        chunks=[]
        for r in rows[:-1]:
            chunks.append(" ".join(str(r.get("thought","")).split())[:90])
        current=self.full[:self.shown]
        chunks.append("▌ "+current)
        self.body.setText("\n\n".join(chunks[-5:]))

class TextPanel(Panel):
    def __init__(self):
        super().__init__("TEXT OUTPUT • G.A.I. WRITINGS")
    def refresh(self):
        p=latest_file(CREATIVE/"text",".txt")
        if p:
            try: self.body.setText(f"{p.name}\n\n{p.read_text()[:900]}")
            except Exception: pass
        else: self.body.setText("No text artifact yet.")

class PixelPanel(Panel):
    def __init__(self):
        super().__init__("PIXELS / DRAWING PAD • G.A.I. OUTPUT")
        self.canvas=QLabel(); self.canvas.setMinimumSize(360,210)
        self.canvas.setStyleSheet("background:#080b10;border-radius:8px;")
        self.layout().addWidget(self.canvas,1)
    def refresh(self):
        img=self.render_art().scaled(self.canvas.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.canvas.setPixmap(QPixmap.fromImage(img))
    def render_art(self):
        img=QImage(480,280,QImage.Format_RGB32); img.fill(QColor("#080b10"))
        p=QPainter(img); p.setRenderHint(QPainter.Antialiasing)
        svg=latest_file(CREATIVE/"paint",".svg") or latest_file(CREATIVE/"images",".svg")
        if svg:
            try:
                text=svg.read_text()
                m=re.search(r'<svg[^>]*width="([^"]+)"[^>]*height="([^"]+)"',text)
                p.setPen(QPen(QColor(70,220,255),2))
                for x1,y1,x2,y2 in re.findall(r'<line[^>]*x1="([^"]+)"[^>]*y1="([^"]+)"[^>]*x2="([^"]+)"[^>]*y2="([^"]+)"',text):
                    p.drawLine(float(x1),float(y1),float(x2),float(y2))
                for pts in re.findall(r'<polyline[^>]*points="([^"]+)"',text):
                    vals=re.findall(r'(-?\d+(?:\.\d+)?)[, ]+(-?\d+(?:\.\d+)?)',pts)
                    if vals:
                        for a,b in zip(vals,vals[1:]): p.drawLine(float(a[0]),float(a[1]),float(b[0]),float(b[1]))
            except Exception: pass
        p.end(); return img

class Cockpit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G.A.I. • Cognitive Cockpit")
        self.resize(900,720)
        self.setStyleSheet("""
        QWidget{background:#0b0e13;color:#dce7f5;}
        QFrame#panel{background:#111720;border:1px solid #253140;border-radius:12px;}
        QLabel#title{color:#70d9ff;font-weight:bold;font-size:11px;letter-spacing:1px;}
        """)
        self.view=Viewfinder(); self.thought=ThoughtPanel(); self.text=TextPanel(); self.pixel=PixelPanel()
        left=QVBoxLayout(); left.addWidget(self.view,2); left.addWidget(self.thought,1)
        right=QVBoxLayout(); right.addWidget(self.text,1); right.addWidget(self.pixel,2)
        root=QHBoxLayout(self); root.setContentsMargins(10,10,10,10); root.setSpacing(10)
        l=QWidget(); l.setLayout(left); r=QWidget(); r.setLayout(right)
        root.addWidget(l,3); root.addWidget(r,2)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(350)
        self.shot=QTimer(self); self.shot.timeout.connect(self.capture); self.shot.start(700)
        self.capture(); self.refresh()
    def capture(self):
        try:
            subprocess.run(["gnome-screenshot","-f",str(SCREEN)],timeout=2,check=False,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except Exception: pass
    def refresh(self):
        self.view.refresh(); self.thought.refresh(); self.text.refresh(); self.pixel.refresh()

app=QApplication([])
w=Cockpit(); w.show()
app.exec()
