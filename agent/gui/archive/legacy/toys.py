from __future__ import annotations
import json, math, sys, time
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
try:
    from PySide6.QtSvg import QSvgRenderer
except Exception:
    QSvgRenderer = None

ROOT=Path("/mnt/gai"); STATE=ROOT/"state"; CREATIVE=ROOT/"creative"; EMBLEMS=ROOT/"assets"/"emblems"

META={
 "view":("VIEW","gai-view.svg","Visual attention"),
 "thought":("THOUGHT","gai-thought.svg","Thought stream"),
 "text":("TEXT","gai-text.svg","Writing"),
 "pixels":("PIXELS","gai-pixels.svg","Image making"),
}

def read(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

class Body(QWidget):
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); cx=w/2; cy=h*.48
        # simple digital body / head
        p.setPen(QPen(QColor("#2d7995"),2)); p.setBrush(QBrush(QColor("#0b1823")))
        p.drawRoundedRect(QRectF(cx-90,cy-120,180,220),55,55)
        p.setBrush(QBrush(QColor("#102636")))
        p.drawEllipse(QRectF(cx-66,cy-92,132,115))
        gaze=read(STATE/"gaze.json")
        gx=max(0,min(1,float(gaze.get("x",.5)))); gy=max(0,min(1,float(gaze.get("y",.5))))
        # Map visual-field gaze to a compact eye direction around the digital head.
        dx=(gx-.5)*22; dy=(gy-.5)*15
        for ex in (cx-36,cx+36):
            p.setPen(QPen(QColor("#4fe3ff"),2)); p.setBrush(QBrush(QColor("#071019")))
            p.drawEllipse(QRectF(ex-20,cy-48,40,30))
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor("#9eeaff")))
            p.drawEllipse(QRectF(ex-7+dx,cy-39+dy,14,14))
        p.setPen(QPen(QColor("#2d7995"),2))
        p.drawLine(QPointF(cx-20,cy+2),QPointF(cx+20,cy+2))
        # body/torso marker
        p.drawLine(QPointF(cx-50,cy+100),QPointF(cx-78,cy+155))
        p.drawLine(QPointF(cx+50,cy+100),QPointF(cx+78,cy+155))
        p.drawLine(QPointF(cx-78,cy+155),QPointF(cx+78,cy+155))
        p.end()

class OrganCard(QFrame):
    def __init__(self,kind):
        super().__init__(); self.kind=kind
        self.setObjectName("card")
        name,icon,_=META[kind]; self.icon_path=EMBLEMS/icon
        self.setMinimumSize(260,120); self.setMaximumHeight(145)
        lay=QHBoxLayout(self); lay.setContentsMargins(14,12,14,12)
        self.icon=QLabel(); self.icon.setFixedSize(52,52)
        if self.icon_path.exists() and QSvgRenderer:
            pm=QPixmap(52,52); pm.fill(Qt.transparent); q=QPainter(pm); QSvgRenderer(str(self.icon_path)).render(q); q.end(); self.icon.setPixmap(pm)
        lay.addWidget(self.icon)
        text=QVBoxLayout()
        self.title=QLabel(name); self.title.setStyleSheet("font-size:15px;font-weight:700;color:#9eeaff;")
        self.desc=QLabel(META[kind][2]); self.desc.setStyleSheet("color:#8298a8;")
        self.content=QLabel("waiting…"); self.content.setWordWrap(True); self.content.setStyleSheet("color:#dce7f5;")
        text.addWidget(self.title); text.addWidget(self.desc); text.addWidget(self.content,1)
        lay.addLayout(text,1)
        self.setStyleSheet("QFrame#card{background:#0b1722;border:1px solid #24566b;border-radius:18px;}")

    def refresh(self):
        if self.kind=="thought":
            rows=[]
            for f in (STATE/"cognitive_core.jsonl",STATE/"autonomous_cognition.jsonl",STATE/"thoughts.jsonl"):
                try: rows=[json.loads(x) for x in f.read_text().splitlines()[-3:]]
                except Exception: rows=[]
                if rows: break
            d=rows[-1] if rows else {}; t=" ".join(str(d.get("thought",d.get("text",""))).split())
            self.content.setText(t[:180] or "waiting…")
        elif self.kind=="text":
            try:
                p=max((x for x in (CREATIVE/"text").glob("*.txt")),key=lambda x:x.stat().st_mtime)
                self.content.setText(p.read_text()[:180].replace("\n"," ") or "waiting…")
            except Exception: self.content.setText("waiting for a text artifact…")
        elif self.kind=="pixels":
            try:
                p=max((x for x in (CREATIVE/"images").glob("*")),key=lambda x:x.stat().st_mtime)
                self.content.setText(p.name)
            except Exception: self.content.setText("ready to create…")
        else:
            try:
                env=read(STATE/"v1_environment.json")
                obj=env.get("object",{})
                self.content.setText(
                    f"object: {obj.get('state','quiet')} • changes {obj.get('changes',0)}"
                )
            except Exception:
                self.content.setText("V1 environment waiting…")

class ToysApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G.A.I. • Digital Body & Organs")
        self.setWindowIcon(QIcon(str(EMBLEMS/"gai-gui.svg")))
        self.setFixedSize(980,650)
        self.setStyleSheet("QWidget{background:#071019;color:#dce7f5;} QLabel{color:#dce7f5;}")
        root=QVBoxLayout(self); root.setContentsMargins(18,18,18,18); root.setSpacing(14)
        head=QHBoxLayout()
        title=QLabel("G.A.I."); title.setStyleSheet("font-size:25px;font-weight:800;color:#9eeaff;")
        sub=QLabel("digital body  •  persistent organs"); sub.setStyleSheet("color:#8298a8;font-size:13px;")
        head.addWidget(title); head.addWidget(sub); head.addStretch(); root.addLayout(head)
        bodyrow=QHBoxLayout(); bodyrow.setSpacing(18)
        self.body=Body(); self.body.setMinimumWidth(360); bodyrow.addWidget(self.body,0)
        cards=QVBoxLayout(); cards.setSpacing(10)
        self.cards={k:OrganCard(k) for k in ("view","thought","text","pixels")}
        for c in self.cards.values(): cards.addWidget(c)
        bodyrow.addLayout(cards,1); root.addLayout(bodyrow,1)
        foot=QLabel("Eyes = attention • toys = capabilities • diagnosis = raw sensory field")
        foot.setAlignment(Qt.AlignCenter); foot.setStyleSheet("color:#597687;font-size:12px;")
        root.addWidget(foot)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(350); self.refresh()

    def refresh(self):
        self.body.update()
        for c in self.cards.values(): c.refresh()

if __name__=="__main__":
    app=QApplication(sys.argv); w=ToysApp(); w.show(); sys.exit(app.exec())
