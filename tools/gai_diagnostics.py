from __future__ import annotations
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QTimer, Qt, QPoint, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QKeySequence, QShortcut,
    QLinearGradient, QRadialGradient, QPainterPath, QFont
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPlainTextEdit, QFrame, QSplitter, QComboBox, QStackedWidget
)

ROOT=Path("/mnt/gai")
try:
    from agent.core.scaling import character_budget, available_worker_steps, worker_ceiling
except ModuleNotFoundError:
    from core.scaling import character_budget, available_worker_steps, worker_ceiling
STATE=ROOT/"state/runtime.json"
FACE=ROOT/"state/face.json"
BODY_OUTPUT=ROOT/"state/body_output.json"

def read_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def keep_screen_on():
    try:
        subprocess.Popen(["xset","s","off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["xset","-dpms"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["xset","s","noblank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

class Expression(QWidget):
    """G.A.I.'s living visual surface. Appearance is driven by runtime phenotype."""
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.face_state={}
        self.t0=time.monotonic()
        self.setStyleSheet("background:#03050a;")
        self.anim=QTimer(self)
        self.anim.timeout.connect(self.update)
        self.anim.start(33)

    def set_state(self,s):
        self.face_state=s or {}

    def _appearance(self):
        a=self.face_state.get("appearance",{}) or {}
        return a if a else {}

    def _palette(self,style):
        return {
            "minimal":("#050912","#b9d7ff","#6ca8ff","#182840"),
            "curious":("#020b10","#d9ffff","#45e6ff","#123e48"),
            "warm":("#0d0904","#fff0c2","#ffbf63","#4a2d12"),
            "alert":("#100304","#ffe1e5","#ff5f70","#4b1018"),
            "quiet":("#08050e","#eee0ff","#aa7dff","#2e1b4c"),
            "dream":("#030817","#d9e4ff","#6f91ff","#18285a"),
        }.get(style,("#050912","#b9d7ff","#6ca8ff","#182840"))

    def _emotion_colour(self,a):
        """Blend the dominant emotional state into the living display colour."""
        curiosity=float(a.get("curiosity",.5) or .5)
        satisfaction=float(a.get("satisfaction",.5) or .5)
        fear=float(a.get("fear",0) or 0)
        stress=float(a.get("stress",0) or 0)
        fatigue=float(a.get("fatigue",0) or 0)
        weights=[
            (fear+stress*0.8,(255,65,82)),
            (curiosity,(40,220,255)),
            (satisfaction,(255,185,70)),
            (fatigue,(150,105,255)),
        ]
        strength,rgb=max(weights,key=lambda x:x[0])
        if strength < .15:
            rgb=(120,165,255)
        return QColor(*rgb)

    def _eye_path(self,cx,cy,w,h,open_amt):
        p=QPainterPath()
        o=max(.04,min(1.0,open_amt))
        p.moveTo(cx-w,cy)
        p.cubicTo(cx-w*.45,cy-h*o,cx+w*.45,cy-h*o,cx+w,cy)
        p.cubicTo(cx+w*.45,cy+h*o,cx-w*.45,cy+h*o,cx-w,cy)
        return p

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        cx,cy=w/2,h/2
        t=time.monotonic()-self.t0

        a=self._appearance()
        toy=read_json(FACE)
        if toy:
            a={**a, **toy}
        style=str(a.get("style","minimal"))
        def num(key, default=0.0):
            try: return float(a.get(key, default) or default)
            except (TypeError, ValueError): return float(default)
        variant=int(num("variant",0))
        curiosity=num("curiosity",.5)
        satisfaction=num("satisfaction",.5)
        happiness=max(-1.0,min(1.0,num("happiness",0.0)))
        boredom=max(0.0,min(1.0,num("boredom",0.0)))
        toy_eye_open=max(0.04,min(1.0,num("eye_open",1.0)))
        toy_eye_offset=max(-1.0,min(1.0,num("eye_offset",0.0)))
        toy_glow=max(0.0,min(1.0,num("glow",0.5)))
        toy_particles=bool(a.get("particles",False))
        fear=num("fear",0)
        stress=num("stress",0)
        fatigue=num("fatigue",0)
        phase=str(a.get("phase",self.face_state.get("lifecycle",{}).get("phase","awake")))

        bg,ink,accent,deep=self._palette(style)
        # Happiness is an ordered visual continuum: happy warms/brightens,
        # sadness cools/dims. Boredom is mildly unpleasant but remains distinct
        # from sadness and never becomes an action command.
        if happiness >= 0:
            hcol=QColor(255,185,70); target_bg=(18+int(10*happiness),14+int(8*happiness),6)
        else:
            hcol=QColor(95,130,255); target_bg=(4,7,18+int(14*(-happiness)))
        bg=QColor(*target_bg).name()
        emotion=self._emotion_colour(a)
        emotion=QColor(
            int(emotion.red()*.55+hcol.red()*.45),
            int(emotion.green()*.55+hcol.green()*.45),
            int(emotion.blue()*.55+hcol.blue()*.45),
        )
        # Emotional colour gently overrides the base palette rather than snapping.
        accent_rgb=emotion
        mix=min(0.78,max(0.18,stress+fear+curiosity+satisfaction+fatigue))
        accent=QColor(
            int(QColor(accent).red()*(1-mix)+emotion.red()*mix),
            int(QColor(accent).green()*(1-mix)+emotion.green()*mix),
            int(QColor(accent).blue()*(1-mix)+emotion.blue()*mix),
        )

        # Brain pulse: tick activity controls the pulse rate. Higher metabolic
        # activity means a faster visual heartbeat, capped for human readability.
        tick=self.face_state.get("tick",{}) or {}
        actual_fps=max(0.0,float(tick.get("actual_fps",tick.get("target_fps",20)) or 0))
        target_fps=max(1.0,float(tick.get("target_fps",20) or 20))
        # Absolute metabolic tick rate drives pulse speed: 20 -> 1.2Hz,
        # 40 -> 2.4Hz, 80 -> 3.6Hz, 160 -> 4.8Hz.
        reference=max(1.0,float(self.face_state.get("tick",{}).get("metabolic_ceiling",20) or 20))
        effective_fps=max(1.0,actual_fps if actual_fps>.1 else target_fps)
        pulse_hz=min(8.0,max(.35,1.2+1.2*math.log2(max(1.0,effective_fps/20.0))))
        brain_load=min(1.0,effective_fps/reference)
        brain_pulse=.5+.5*math.sin(t*2*math.pi*pulse_hz)
        breathe=.5+.5*math.sin(t*1.15)
        glow=((0.10+0.10*breathe)+(0.16*stress)+(0.10*curiosity)+(0.12*brain_pulse*brain_load))*toy_glow
        p.fillRect(0,0,w,h,QColor(bg))
        rg=QRadialGradient(QPointF(cx,cy),min(w,h)*(.44+.08*brain_pulse))
        c=QColor(accent); c.setAlphaF(min(.48,glow))
        rg.setColorAt(0,c); c2=QColor(accent); c2.setAlphaF(0)
        rg.setColorAt(1,c2)
        p.fillRect(0,0,w,h,rg)

        # Variant changes the silhouette slowly across dream cycles.
        if style in ("curious","dream") or variant in (2,5):
            pen=QPen(QColor(accent)); pen.setWidth(max(2,int(min(w,h)*.004)))
            pen.setColor(QColor(accent)); p.setPen(pen)
            for ring in range(1,3):
                r=min(w,h)*(.23+ring*.045)
                alpha=max(20,70-ring*18)
                col=QColor(accent); col.setAlpha(alpha); p.setPen(QPen(col,2))
                p.drawEllipse(QPointF(cx,cy),r,r)

        # Subtle orbit particles — visual movement without becoming a game HUD.
        if style=="curious" or toy_particles:
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(accent)))
            for i in range(3):
                ang=t*(.35+i*.09)+i*2.1
                rr=min(w,h)*(.27+i*.035)
                px=cx+math.cos(ang)*rr; py=cy+math.sin(ang)*rr*.52
                p.drawEllipse(QPointF(px,py),3,3)

        eye_y=cy-min(w,h)*.105
        eye_dx=min(w,h)*(.135+.035*curiosity)
        eye_w=min(w,h)*(.045)
        eye_h=min(w,h)*(.038)

        # Slow blink: the eye geometry closes first, then fades almost to black.
        blink_phase=(t % 6.7)
        blink_window=.62
        blink_dist=abs(blink_phase-5.95)
        blink=min(1.0,max(0.0,1.0-blink_dist/(blink_window*.5)))
        blink_smooth=0.5-0.5*math.cos(math.pi*blink)
        # Positive valence gently opens/brightens the eyes; negative valence
        # makes them heavier without forcing a discrete facial state.
        openness=max(.04,1.0-fatigue*.68 + .12*happiness - .10*boredom)*toy_eye_open
        if phase=="dream" or style=="dream":
            openness=.10*toy_eye_open
        visual_open=openness*(1.0-.97*blink_smooth)
        eye_alpha=int(255*(.10+.90*max(0.0,visual_open)))
        if style=="alert":
            visual_open=min(1.0,visual_open*1.28)

        eye_col=QColor(ink); eye_col.setAlpha(max(8,min(255,eye_alpha)))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(eye_col))
        for side in (-1,1):
            ex=cx+side*eye_dx + toy_eye_offset*min(w,h)*.04
            if style in ("curious","warm","alert"):
                p.drawPath(self._eye_path(ex,eye_y,eye_w,eye_h,visual_open))
            elif style=="quiet" or phase=="dream":
                line=QColor(ink); line.setAlpha(max(8,eye_alpha))
                p.setPen(QPen(line,max(3,int(min(w,h)*.008*max(.15,visual_open)))))
                p.drawLine(QPointF(ex-eye_w,eye_y),QPointF(ex+eye_w,eye_y))
                p.setPen(Qt.NoPen)
            else:
                p.drawEllipse(QPointF(ex,eye_y),eye_w,eye_h*max(.04,visual_open))

        # Pupils track curiosity and gently wander when awake.
        look_x=(curiosity-.5)*min(w,h)*.022
        wander=math.sin(t*.55)*min(w,h)*.006
        look_y=math.sin(t*.31)*min(w,h)*.004
        pupil=min(w,h)*(.012+.006*curiosity)*max(.15,visual_open)
        pupil_col=QColor(deep); pupil_col.setAlpha(max(8,eye_alpha))
        p.setBrush(QBrush(pupil_col))
        if style!="quiet" and phase!="dream":
            for side in (-1,1):
                ex=cx+side*eye_dx
                p.drawEllipse(QPointF(ex+look_x+wander,eye_y+look_y),pupil,pupil)

        # The mouth is a speaker indicator, not an emotion indicator.
        # It is CLOSED unless G.A.I.'s own output channel explicitly reports
        # active sound. Microphone input never opens the mouth.
        body=read_json(BODY_OUTPUT)
        output_active=bool(body.get("audio_active",False))
        rms=max(0.0,min(1.0,float(body.get("rms",0.0) or 0.0))) if output_active else 0.0
        peak=max(rms,min(1.0,float(body.get("peak",rms) or rms))) if output_active else 0.0
        talking=output_active and (rms>.005 or peak>.01)
        mouth_y=cy+min(w,h)*.115
        mw=min(w,h)*(.105+.045*satisfaction)
        mh=min(w,h)*(.035+.025*stress)
        pen=QPen(QColor(ink),max(4,int(min(w,h)*.009)))
        p.setPen(pen); p.setBrush(Qt.NoBrush)

        if talking:
            # The only mouth animation is a waveform driven by speaker output.
            open_amt=max(.04,min(1.0,rms*8.0+peak*.5))
            amp=mh*(0.8+2.8*open_amt)
            half=mw*(0.65+0.35*open_amt)
            path=QPainterPath(); steps=48
            for i in range(steps+1):
                u=i/steps
                x=cx-half+2*half*u
                y=mouth_y + math.sin(t*18.0 + u*math.pi*4.0)*(amp*(0.35+0.65*u))
                if i==0: path.moveTo(x,y)
                else: path.lineTo(x,y)
            col=QColor(accent); col.setAlpha(int(100+140*open_amt))
            p.setPen(QPen(col,max(3,int(min(w,h)*.006)))); p.setBrush(Qt.NoBrush); p.drawPath(path)
        else:
            # Emotion cannot open or animate the mouth. Silence = closed.
            p.setPen(QPen(QColor(ink),max(4,int(min(w,h)*.009))))
            p.drawLine(QPointF(cx-mw*.55,mouth_y),QPointF(cx+mw*.55,mouth_y))

        # Tiny state indicator: a breathing point, not a debug panel.
        pulse=0.5+0.5*math.sin(t*2.0)
        dot=QColor(accent); dot.setAlpha(int(80+100*pulse))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(dot))
        p.drawEllipse(QPointF(cx,cy+min(h*.22,170)),3.0+2*pulse,3.0+2*pulse)

        # Minimal identity footer.
        p.setPen(QColor(150,160,180))
        p.setFont(QFont("Sans",10))
        mode=str(a.get("mode",self.face_state.get("state",{}).get("mode","idle")))
        p.drawText(0,h-48,w,24,Qt.AlignCenter,f"G.A.I.  •  {phase.upper()}  •  {mode}")
        p.setPen(QColor(95,105,125))
        p.drawText(0,h-24,w,18,Qt.AlignCenter,"Ctrl+D  ·  diagnostics")

class Card(QFrame):
    def __init__(self,title):
        super().__init__(); self.setObjectName("card")
        lay=QVBoxLayout(self); lay.setContentsMargins(16,12,16,12); lay.setSpacing(6)
        self.title=QLabel(title); self.title.setObjectName("cardTitle")
        self.value=QLabel("—"); self.value.setObjectName("cardValue")
        self.detail=QLabel(""); self.detail.setObjectName("detail"); self.detail.setWordWrap(True)
        lay.addWidget(self.title); lay.addWidget(self.value); lay.addWidget(self.detail)

class LayerBar(QWidget):
    """Always-visible map of the cognitive/body pipeline, including fast layers."""
    LAYERS=(
        ("SENSE","#4fc3f7"),("BODY","#81c784"),("FEEL","#f06292"),
        ("TENDENCY","#ba68c8"),("WORLD","#64b5f6"),("CHOICE","#9575cd"),
        ("ACTION","#ff8a65"),("OUTCOME","#ffd54f"),("MEMORY","#26a69a"),
        ("DREAM","#7986cb"),
    )
    def __init__(self):
        super().__init__(); self.values={name:0.0 for name,_ in self.LAYERS}; self.setMinimumHeight(58)
    def set_values(self, values):
        self.values.update({k:max(0.0,min(1.0,float(v))) for k,v in values.items()}); self.update()
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); n=len(self.LAYERS); gap=3; x=0
        p.setFont(QFont("Sans",8))
        for name,hexcol in self.LAYERS:
            seg=(w-gap*(n-1))/n; v=self.values.get(name,0.0)
            col=QColor(hexcol); p.setPen(Qt.NoPen)
            bg=QColor(35,39,48); p.setBrush(QBrush(bg)); p.drawRoundedRect(int(x),0,int(seg),28,4,4)
            col.setAlpha(int(55+200*v)); p.setBrush(QBrush(col)); p.drawRoundedRect(int(x+2),2,int(max(2,seg-4)*max(.06,v)),24,3,3)
            p.setPen(QColor(215,220,230)); p.drawText(int(x),34,int(seg),18,Qt.AlignCenter,name)
            x += seg+gap

class Monitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G.A.I. — Diagnostic Console")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.resize(1200, 800)
        self.move(120, 80)
        self._drag_offset = None
        self._last_ai_position = None
        self.stack=QStackedWidget(); self.setCentralWidget(self.stack)
        self.expression=Expression(); self.stack.addWidget(self.expression)
        self.debug=self.build_debug(); self.stack.addWidget(self.debug)
        self.stack.setCurrentIndex(1)
        self.shortcut=QShortcut(QKeySequence("Ctrl+D"),self); self.shortcut.activated.connect(self.toggle_debug)
        cfg=read_json(ROOT/"config/agent.json")
        self.state_timer=QTimer(self); self.state_timer.timeout.connect(self.refresh)
        self.state_timer.start(max(50,round(1000/float(cfg.get("gui_refresh_hz",10)))))
        self.refresh()
        keep_screen_on()
        self.keepalive=QTimer(self); self.keepalive.timeout.connect(keep_screen_on); self.keepalive.start(30000)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def set_ai_position(self, x, y):
        """Allow the organism to reposition its own visual bubble safely."""
        try:
            x, y = int(x), int(y)
            screen = QApplication.primaryScreen().availableGeometry()
            x = max(screen.left(), min(x, screen.right() - self.width()))
            y = max(screen.top(), min(y, screen.bottom() - self.height()))
            self.move(x, y)
            self._last_ai_position = (x, y)
        except Exception:
            pass

    def toggle_debug(self):
        self.stack.setCurrentIndex(0 if self.stack.currentIndex()==1 else 1)
        self.setWindowTitle("G.A.I. — Debug Monitor" if self.stack.currentIndex() else "G.A.I.")

    def build_debug(self):
        root=QWidget(); outer=QVBoxLayout(root); outer.setContentsMargins(18,18,18,18); outer.setSpacing(12)
        header=QHBoxLayout(); self.title=QLabel("G.A.I."); self.title.setObjectName("mainTitle")
        self.phase=QLabel("● AWAKE"); self.phase.setObjectName("phase"); self.uptime=QLabel("")
        header.addWidget(self.title); header.addStretch(); header.addWidget(self.phase); header.addSpacing(18); header.addWidget(self.uptime); outer.addLayout(header)
        cards=QGridLayout(); cards.setSpacing(10); self.cards={}
        for i,(key,label) in enumerate([
            ("battery","POWER"),("cpu","CPU"),("memory","MEMORY"),("camera","VISION"),
            ("audio","HEARING"),("mode","CURRENT MODE"),("reward","REWARD"),("prediction","PREDICTION"),
            ("energy","ENERGY"),("rest","REST NEED"),("stress","STRESS"),("processing","PROCESSING")
        ]):
            c=Card(label); self.cards[key]=c; cards.addWidget(c,i//4,i%4)
        outer.addLayout(cards)
        layer_head=QHBoxLayout()
        layer_head.addWidget(QLabel("Cognitive / metabolic pipeline  •  intensity = current activity"))
        layer_head.addStretch(); layer_head.addWidget(QLabel("fast layers remain visible"))
        outer.addLayout(layer_head)
        self.layer_bar=LayerBar(); outer.addWidget(self.layer_bar)
        self.layer_key=QLabel("Sense  •  Body  •  Feel  •  Tendency  •  World model  •  Choice  •  Action  •  Outcome  •  Memory  •  Dream")
        self.layer_key.setObjectName("layerKey"); self.layer_key.setWordWrap(True); outer.addWidget(self.layer_key)
        split=QSplitter(Qt.Horizontal)
        left=QWidget(); ll=QVBoxLayout(left); ll.addWidget(QLabel("Nervous System")); self.components=QPlainTextEdit(); self.components.setReadOnly(True); ll.addWidget(self.components); split.addWidget(left)
        right=QWidget(); rl=QVBoxLayout(right); rl.addWidget(QLabel("Live Neural Traffic")); self.events=QPlainTextEdit(); self.events.setReadOnly(True); rl.addWidget(self.events); split.addWidget(right); split.setSizes([500,800]); outer.addWidget(split,1)
        bottom=QHBoxLayout()
        self.drives=QLabel("Drives: —"); self.sleep=QLabel("Sleep: —"); self.storage=QLabel("Storage: —"); self.appearance=QLabel("Appearance: —"); self.tick_label=QLabel("Metabolic workers • 50 chars/MW")
        self.tick_selector=QComboBox(); self.tick_selector.setFixedWidth(80); self.update_tick_options(); self.tick_selector.currentTextChanged.connect(self.set_tick_workers)
        for x in (self.drives,self.sleep,self.storage,self.appearance): x.setObjectName("bottom")
        bottom.addWidget(self.drives); bottom.addStretch(); bottom.addWidget(self.sleep); bottom.addStretch(); bottom.addWidget(self.storage); bottom.addStretch(); bottom.addWidget(self.appearance); bottom.addStretch(); bottom.addWidget(self.tick_label); bottom.addWidget(self.tick_selector); outer.addLayout(bottom)
        root.setStyleSheet("""QWidget{background:#101218;color:#e8eaf0} QFrame#card{background:#191d26;border:1px solid #2b3140;border-radius:12px} QLabel#cardTitle{color:#8f97aa;font-size:11px;font-weight:700} QLabel#cardValue{color:#f4f6fb;font-size:24px;font-weight:700} QLabel#detail{color:#aeb5c5;font-size:11px} QLabel#mainTitle{font-size:30px;font-weight:800} QLabel#phase{font-size:15px;font-weight:800;color:#74e0a1} QPlainTextEdit{background:#151820;border:1px solid #2b3140;border-radius:10px;color:#dce1eb;font-family:monospace;font-size:12px} QLabel#bottom{color:#aeb5c5;font-size:12px}""")
        return root

    def update_tick_options(self):
        cfg=read_json(ROOT/"config/agent.json"); opts=[f"{w} MW" for w in available_worker_steps()]
        self.tick_selector.blockSignals(True); self.tick_selector.clear(); self.tick_selector.addItems(opts)
        wanted=f"{int(cfg.get('metabolic_workers',1))} MW"
        self.tick_selector.setCurrentText(wanted if wanted in opts else "1 MW")
        self.tick_selector.blockSignals(False)

    def set_tick_workers(self,value):
        try: workers=int(str(value).split()[0])
        except (ValueError,IndexError): return
        if workers<1:return
        cfg=read_json(ROOT/"config/agent.json"); cfg["metabolic_workers"]=workers
        cfg["tick_fps"]=cfg.get("metabolic_base_fps",20)*workers; cfg["gui_refresh_hz"]=10
        (ROOT/"config/agent.json").write_text(json.dumps(cfg,indent=2)+"\n")

    def set_card(self,key,value,detail=""):
        self.cards[key].value.setText(str(value)); self.cards[key].detail.setText(detail)

    def refresh(self):
        s=read_json(STATE); cfg=read_json(ROOT/"config/agent.json")
        self.expression.set_state(s)
        self.state_timer.setInterval(max(50,round(1000/float(cfg.get("gui_refresh_hz",10)))))
        if not s:return
        tick=s.get("tick",{}); lifecycle=s.get("lifecycle",{}); st=s.get("state",{}); nerv=s.get("nervous",{}); world=s.get("world",{}); perc=s.get("perception",{})
        phase=lifecycle.get("phase","awake").upper(); self.phase.setText(f"● {phase}"); self.uptime.setText("uptime %.1fs"%float(st.get("uptime",0)))
        obs=world.get("last_observation") or {}; sysd=obs.get("system") or {}
        self.set_card("battery",f"{lifecycle.get('battery',0)*100:.0f}%","charging" if lifecycle.get("charging") else "on battery")
        self.set_card("cpu",f"{float(sysd.get('load_1m',0)):.2f}","1-minute load")
        mem=sysd.get("memory_available"); total=sysd.get("memory_total")
        self.set_card("memory",f"{(1-mem/total)*100:.0f}%" if mem and total else "—",f"{mem/1024/1024/1024:.1f} GiB available" if mem else "")
        cam=bool(perc.get("senses",{}).get("camera")); self.set_card("camera","ONLINE" if cam else "OFFLINE",f"{world.get('observation_count',0)} observations")
        aud=perc.get("senses",{}).get("audio",{}) or {}; self.set_card("audio",f"{float(aud.get('rms',0)):.2f}",f"peak {float(aud.get('peak',0)):.2f}")
        self.set_card("mode",st.get("mode","—"),s.get("action",{}).get("reason",""))
        self.set_card("reward",f"{float(s.get('action',{}).get('expected_reward',0)):.3f}","expected action reward")
        self.set_card("prediction",str(len(s.get("predictions",{}))),"learned action/context models")
        needs=s.get("core_needs",{}) or {}
        mot=s.get("motivation",{}) or {}
        emotions=mot.get("emotions",{}) or {}
        self.set_card("energy",f"{float(needs.get('energy',0))*100:.0f}%","body energy")
        self.set_card("rest",f"{float(needs.get('rest',0))*100:.0f}%","accumulated body rest debt")
        self.set_card("processing",f"{float(needs.get('processing',0))*100:.0f}%","system load / CPU capacity")
        self.set_card("stress",f"{float(st.get('stress',0))*100:.0f}%",f"fear {float(emotions.get('fear',0))*100:.0f}%")
        self.set_card("processing",f"{float(needs.get('processing',0))*100:.0f}%","system load / CPU capacity")

        # A compact live map of the organism's actual causal loop.
        organs=((s.get("sensory",{}) or {}).get("organs",{}) or {})
        layer_values={
            "SENSE": 1.0 if any((o.get("status") == "active") for o in organs.values() if isinstance(o,dict)) else 0.0,
            "BODY": max(float(needs.get("power",0)), float(needs.get("energy",0)),
                        float(needs.get("sleep_need",0)), float(needs.get("processing",0))),
            "FEEL": max(float(st.get("happiness",0.0)) if float(st.get("happiness",0.0)) > 0 else 0.0,
                        float(st.get("stress",0.0)), float(st.get("boredom",0.0))),
            "TENDENCY": max((float(v) for v in (s.get("drives",{}) or {}).values()), default=0.0),
            "WORLD": min(1.0, float(s.get("latest_prediction_error",0.0) or 0.0) * 2.0),
            "CHOICE": min(1.0, abs(float(s.get("control",{}).get("score",0.0) or 0.0)) / 2.0),
            "ACTION": min(1.0, abs(float(s.get("action",{}).get("score",0.0) or 0.0)) / 2.0),
            "OUTCOME": min(1.0, abs(float(s.get("latest_reward",0.0) or 0.0))),
            "MEMORY": min(1.0, float((s.get("working_memory",{}) or {}).get("size",0) or 0) / 32.0),
            "DREAM": 1.0 if phase.lower() in {"dream","pre_sleep"} else 0.0,
        }
        self.layer_bar.set_values(layer_values)
        comps=nerv.get("components",{}); lines=[]
        for name,data in comps.items():
            if "." in name:continue
            age=max(0,datetime.now().timestamp()-float(data.get("last_heartbeat",0)))
            lines.append(f"{data.get('state','?'):>9}  {name:<16} {data.get('kind',''):>9}  hb {age:4.1f}s")
        self.components.setPlainText("\n".join(lines) or "No components")
        m=nerv.get("metrics",{})
        self.events.setPlainText(
            f"published: {m.get('published',0)}   delivered: {m.get('delivered',0)}   dropped: {m.get('dropped',0)}   errors: {m.get('errors',0)}\n\n"
            f"Core heartbeat: {comps.get('kernel',{}).get('state','unknown')}\n"
            f"Tick: {tick.get('actual_fps',0):.1f}/{tick.get('target_fps',20)} FPS\n"
            f"Metabolic workers: {tick.get('metabolic_workers',1)}"
        )
        drives=s.get("drives",{})
        self.drives.setText("Drives  "+"  ".join(f"{k}:{float(v):.2f}" for k,v in drives.items()))
        self.sleep.setText(f"Sleep  {phase.lower()}  •  need {float(needs.get('sleep_need',0))*100:.0f}%  •  cycles {lifecycle.get('dream_cycles',0)}")
        disk=float(sysd.get("disk_free_gai",0)); self.storage.setText(f"Storage  {disk/1024/1024/1024:.0f} GiB free")
        app=s.get("appearance",{}) or {}; self.appearance.setText(f"Look  {app.get('style','—')}  v{app.get('variant','—')}")

def main():
    app=QApplication(sys.argv)
    win=Monitor(); win.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())
