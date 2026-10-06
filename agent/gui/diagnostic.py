from __future__ import annotations
import json, time, uuid, shutil, os, fcntl
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QPushButton, QToolButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QComboBox,
    QSizePolicy, QScrollArea, QProgressBar
)
from gui.theme import apply

ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
RUNTIME = STATE / "runtime.json"
EVENT_LOG = STATE / "events.jsonl"
ACTIVE = STATE / "gai_active.json"
PROPRIO = STATE / "proprioception.json"
MOTOR = STATE / "motor_output.json"
BODY = STATE / "body_output.json"
INTERACTION = STATE / "toy_interaction.json"
OUTPUTS = STATE / "output_windows.json"
AUDIO = STATE / "audio_input.json"
DEEP = ROOT / "storage/simulated_hdd/deep_storage"
LOG = ROOT / "logs/launcher.log"
SPEED = STATE / "simulation_speed.json"
COMMAND = STATE / "user_command.json"
RESULT = STATE / "user_command_result.json"
SPEEDS = (0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)

CYAN = "#62d9ff"
CYAN2 = "#2b91b8"
BLUE = "#10283a"
BG = "#050b12"
PANEL = "#081521"
PANEL2 = "#0b1b28"
TEXT = "#e4edf4"
MUTED = "#7893a7"
GREEN = "#59e39a"
RED = "#ff6570"
GOLD = "#e7c98c"

def jread(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def num(v, d=0.0):
    try: return float(v)
    except Exception: return d

def age(ts):
    return max(0, time.time() - num(ts, time.time())) if ts else None

class GlowFrame(QFrame):
    def __init__(self, title="", subtitle=""):
        super().__init__()
        self.setObjectName("panel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 13, 16, 14)
        self.layout.setSpacing(7)
        if title:
            row = QHBoxLayout()
            t = QLabel(title.upper())
            t.setObjectName("panelTitle")
            row.addWidget(t)
            row.addStretch()
            if subtitle:
                s = QLabel(subtitle)
                s.setObjectName("panelMeta")
                row.addWidget(s)
            self.layout.addLayout(row)

class Meter(QProgressBar):
    def __init__(self, value=0):
        super().__init__()
        self.setRange(0,100)
        self.setValue(max(0,min(100,int(num(value)*100))))
        self.setTextVisible(False)
        self.setFixedHeight(7)
        self.setObjectName("meter")

class Diagnostic(QWidget):
    """External diagnostic instrument. It observes G.A.I.; it is not an organ."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G.A.I. Diagnostic Instruments")
        self.resize(1280, 860)
        self.setMinimumSize(1050, 700)
        self.setFocusPolicy(Qt.StrongFocus)
        self.data = {}
        self.events = []
        self.current_page = 0
        self.nav = []
        self._build()
        self._load_speed()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def _build(self):
        self.setStyleSheet(f"""
        QWidget {{ background:{BG}; color:{TEXT}; font-family:'DejaVu Sans'; }}
        QFrame#panel {{ background:{PANEL}; border:1px solid #173a50; border-radius:14px; }}
        QLabel#title {{ color:{CYAN}; font-size:20px; font-weight:800; letter-spacing:1px; }}
        QLabel#sub {{ color:{MUTED}; font-size:10px; }}
        QLabel#panelTitle {{ color:{CYAN}; font-size:10px; font-weight:800; letter-spacing:1px; }}
        QLabel#panelMeta {{ color:{MUTED}; font-size:9px; }}
        QLabel#value {{ color:{TEXT}; font-size:12px; font-weight:700; }}
        QLabel#muted {{ color:{MUTED}; font-size:9px; }}
        QLabel#status {{ color:{GREEN}; font-size:10px; font-weight:800; }}
        QLabel#statusBad {{ color:{RED}; font-size:10px; font-weight:800; }}
        QPushButton, QToolButton {{
            background:{PANEL2}; color:#b9eaff; border:1px solid #1c526d;
            border-radius:9px; padding:8px 11px; font-weight:700;
        }}
        QPushButton:hover, QToolButton:hover {{ background:#123149; border:1px solid {CYAN2}; }}
        QPushButton:checked, QToolButton:checked {{ background:#123c52; color:#eaffff; border:1px solid {CYAN}; }}
        QPushButton#suggest {{ background:#102b3c; border:1px solid #2b7898; color:{CYAN}; }}
        QPushButton#suggest:hover {{ background:#16445c; }}
        QComboBox {{ background:{PANEL2}; color:{CYAN}; border:1px solid #1c526d; border-radius:8px; padding:7px 10px; }}
        QComboBox QAbstractItemView {{ background:{PANEL2}; color:{TEXT}; }}
        QProgressBar#meter {{ background:#142735; border:0; border-radius:4px; }}
        QProgressBar#meter::chunk {{ background:{CYAN}; border-radius:4px; }}
        QScrollArea {{ border:0; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel("G.A.I. DIAGNOSTIC INSTRUMENTS")
        title.setObjectName("title")
        brand.addWidget(title)
        sub = QLabel("external observer  •  does not participate in cognition")
        sub.setObjectName("sub")
        brand.addWidget(sub)
        header.addLayout(brand)
        header.addStretch()

        self.phase = QLabel("●  CONNECTING")
        self.phase.setObjectName("status")
        header.addWidget(self.phase)
        self.speed_box = QComboBox()
        self.speed_box.addItems([f"×{x:g}" for x in SPEEDS])
        self.speed_box.setFixedWidth(92)
        self.speed_box.currentIndexChanged.connect(self.set_speed)
        header.addWidget(self.speed_box)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(12)

        side = GlowFrame("INSTRUMENT", "NAV")
        side.setFixedWidth(205)
        self.nav_layout = side.layout
        self.nav_layout.addSpacing(2)
        for i, label in enumerate(["Overview", "Neural Layer", "Nervous System", "Cognition", "Senses & Body", "Memory", "Outputs", "Lab / Evidence"]):
            b = QPushButton(f"{i+1:02d}  {label}")
            b.setCheckable(True)
            b.clicked.connect(lambda checked, idx=i: self.show_page(idx))
            self.nav.append(b)
            self.nav_layout.addWidget(b)
        self.nav_layout.addStretch()
        sep = QLabel("SUGGEST")
        sep.setObjectName("panelTitle")
        self.nav_layout.addWidget(sep)
        for label, cmd in [("Observe / move", "move"), ("Suggest sleep", "sleep"), ("Suggest wake", "wake")]:
            b = QPushButton(label)
            b.setObjectName("suggest")
            b.clicked.connect(lambda checked=False, c=cmd: self.suggest(c))
            self.nav_layout.addWidget(b)
        self.result_label = QLabel("G.A.I. decides whether a suggestion is accepted.")
        self.result_label.setWordWrap(True)
        self.result_label.setObjectName("muted")
        self.nav_layout.addWidget(self.result_label)
        self.nav_layout.addSpacing(5)
        refresh = QPushButton("↻  Refresh now")
        refresh.clicked.connect(self.refresh)
        self.nav_layout.addWidget(refresh)
        body.addWidget(side)

        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self.pages = [
            self.page_overview(), self.page_neural_layer(), self.page_nervous(), self.page_cognition(),
            self.page_senses(), self.page_memory(), self.page_outputs(), self.page_lab()
        ]
        for p in self.pages:
            self.stack.addWidget(p)
        self.show_page(0)

    def make_scroll(self, content):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def grid_page(self):
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(2,2,8,2)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(10)
        return w, g

    def add_panel(self, g, panel, r, c, rs=1, cs=1):
        g.addWidget(panel, r, c, rs, cs)
        return panel

    def line(self, text, bold=False):
        l = QLabel(text)
        l.setWordWrap(True)
        l.setObjectName("value" if bold else "muted")
        return l

    def page_overview(self):
        w,g=self.grid_page()
        self.ov_cc=self.add_panel(g,GlowFrame("01 • CENTRAL CIRCUIT","LIVE"),0,0)
        self.ov_neural=self.add_panel(g,GlowFrame("02 • NERVOUS SYSTEM","TRANSPORT"),0,1)
        self.ov_state=self.add_panel(g,GlowFrame("03 • INTERNAL STATE","DRIVES"),0,2)
        self.ov_sense=self.add_panel(g,GlowFrame("04 • SENSORY ORGANS","INPUT"),1,0)
        self.ov_health=self.add_panel(g,GlowFrame("05 • ORGAN HEALTH","V1"),1,1)
        self.ov_flow=self.add_panel(g,GlowFrame("06 • LIVE FLOW","EVIDENCE"),1,2)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_neural_layer(self):
        w,g=self.grid_page()
        self.neural_overview=self.add_panel(g,GlowFrame("NEURAL FABRIC","CORE"),0,0)
        self.neural_topology=self.add_panel(g,GlowFrame("TOPOLOGY","EDGES"),0,1)
        self.neural_lifecycle=self.add_panel(g,GlowFrame("LIFECYCLE","PHYSIOLOGY"),0,2)
        self.neural_evidence=self.add_panel(g,GlowFrame("GENERATION / EVIDENCE","VALIDATION"),1,0,1,3)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_nervous(self):
        w,g=self.grid_page()
        self.neural_metrics=self.add_panel(g,GlowFrame("EVENT TRANSPORT","BUS"),0,0,1,2)
        self.neural_events=self.add_panel(g,GlowFrame("EVENT STREAM","LATEST"),1,0,2,2)
        self.neural_components=self.add_panel(g,GlowFrame("COMPONENT HEALTH","CELLS"),0,2,3,1)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_cognition(self):
        w,g=self.grid_page()
        self.cog_thought=self.add_panel(g,GlowFrame("CENTRAL CIRCUIT","THOUGHT"),0,0,2,2)
        self.cog_state=self.add_panel(g,GlowFrame("INTERNAL STATE","DRIVES"),0,2)
        self.cog_needs=self.add_panel(g,GlowFrame("CORE NEEDS","METABOLISM"),1,2)
        self.cog_history=self.add_panel(g,GlowFrame("RECENT COGNITION","TRACE"),2,0,1,3)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_senses(self):
        w,g=self.grid_page()
        self.sense_vision=self.add_panel(g,GlowFrame("VISION","SIGHT ORGAN"),0,0)
        self.sense_hearing=self.add_panel(g,GlowFrame("HEARING","AUDIO INPUT"),0,1)
        self.sense_camera=self.add_panel(g,GlowFrame("CAMERA","HARDWARE"),0,2)
        self.sense_body=self.add_panel(g,GlowFrame("BODY / PROPRIOCEPTION","POSITION"),1,0)
        self.sense_motor=self.add_panel(g,GlowFrame("MOTOR SYSTEM","OUTPUT"),1,1)
        self.sense_attention=self.add_panel(g,GlowFrame("ATTENTION / INTERACTION","FOCUS"),1,2)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_memory(self):
        w,g=self.grid_page()
        self.mem_work=self.add_panel(g,GlowFrame("WORKING MEMORY","SHORT TERM"),0,0)
        self.mem_long=self.add_panel(g,GlowFrame("LONG-TERM MEMORY","VALIDATED"),0,1)
        self.mem_deep=self.add_panel(g,GlowFrame("DEEP STORAGE","SSD / ARCHIVE"),0,2)
        self.mem_flow=self.add_panel(g,GlowFrame("MEMORY PIPELINE","PROVENANCE"),1,0,1,3)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_outputs(self):
        w,g=self.grid_page()
        self.out_windows=self.add_panel(g,GlowFrame("TOY / OUTPUT ORGANS","WINDOWS"),0,0,2,1)
        self.out_audio=self.add_panel(g,GlowFrame("AUDIO OUTPUT","SPEAKER"),0,1)
        self.out_motor=self.add_panel(g,GlowFrame("MOTOR OUTPUT","COMMAND"),1,1)
        self.out_inter=self.add_panel(g,GlowFrame("INTERACTION","TOY FOCUS"),0,2,2,1)
        for col in range(3): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def page_lab(self):
        w,g=self.grid_page()
        self.lab_session=self.add_panel(g,GlowFrame("EXPERIMENT / SESSION","CONTROL"),0,0)
        self.lab_event=self.add_panel(g,GlowFrame("LATEST EVIDENCE","EVENT"),0,1)
        self.lab_resources=self.add_panel(g,GlowFrame("METABOLISM / RESOURCES","MACHINE"),1,0)
        self.lab_archive=self.add_panel(g,GlowFrame("DIAGNOSTIC INTEGRITY","EXTERNAL"),1,1)
        for col in range(2): g.setColumnStretch(col,1)
        return self.make_scroll(w)

    def clear_panel(self, panel):
        while panel.layout.count() > 1:
            item=panel.layout.takeAt(1)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub=item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

    def add_text(self,panel,text,bold=False):
        panel.layout.addWidget(self.line(text,bold))

    def add_meter(self,panel,label,value):
        row=QHBoxLayout()
        lab=QLabel(label.upper()); lab.setObjectName("muted"); lab.setFixedWidth(88)
        row.addWidget(lab)
        row.addWidget(Meter(value),1)
        val=QLabel(f"{num(value):.2f}"); val.setObjectName("muted"); row.addWidget(val)
        panel.layout.addLayout(row)

    def refresh(self):
        self.data=jread(RUNTIME)
        self.events=self._events()
        self._update_pages()
        self.update()

    def _events(self):
        out=[]
        try:
            for line in EVENT_LOG.read_text().splitlines()[-100:]:
                try: out.append(json.loads(line))
                except Exception: pass
        except Exception: pass
        latest=((self.data.get("nervous") or {}).get("latest_events") or [])
        known={(e.get("event_id"),e.get("timestamp")) for e in out}
        out += [e for e in latest if (e.get("event_id"),e.get("timestamp")) not in known]
        return sorted(out,key=lambda e:num(e.get("timestamp")),reverse=True)[:24]

    def _update_pages(self):
        active=bool(jread(ACTIVE).get("active"))
        state=self.data.get("state") or {}
        nervous=self.data.get("nervous") or {}
        comps=nervous.get("components") or {}
        senses=self.data.get("world",{}).get("last_observation",{}).get("senses") or {}
        world=self.data.get("world",{}).get("last_observation") or {}
        thoughts=self.data.get("thoughts") or {}
        needs=self.data.get("core_needs") or {}
        perf=world.get("system") or {}
        hw=world.get("hardware") or {}
        latest=self.events[0] if self.events else {}
        intent=(latest.get("payload") or {}).get("intention") or {}
        motor=jread(MOTOR); prop=jread(PROPRIO); body=jread(BODY); inter=jread(INTERACTION)
        outputs=jread(OUTPUTS)
        cc=comps.get("cognitive_core",{})
        m=nervous.get("metrics") or {}
        self.phase.setText(("●  RUNNING" if active else "●  OFF")+"  •  "+str((self.data.get("sensory") or {}).get("phase","unknown")))
        self.phase.setObjectName("status" if active else "statusBad")
        self.phase.style().unpolish(self.phase); self.phase.style().polish(self.phase)

        # Overview
        for p in [self.ov_cc,self.ov_neural,self.ov_state,self.ov_sense,self.ov_health,self.ov_flow]: self.clear_panel(p)
        self.ov_cc.layout.addWidget(self.line("HEALTHY" if cc and not cc.get("error_count") else "DEGRADED",True))
        recent=(thoughts.get("recent") or [{}])
        thought=(recent[-1].get("text") if recent else None) or (latest.get("payload") or {}).get("thought") or "—"
        self.add_text(self.ov_cc,"last thought  "+thought[:130])
        self.add_text(self.ov_cc,"intention  "+str(intent.get("type","—")))
        self.add_text(self.ov_cc,"confidence  "+str((latest.get("payload") or {}).get("confidence","—")))
        self.add_text(self.ov_neural,f"published  {m.get('published',0)}")
        self.add_text(self.ov_neural,f"delivered  {m.get('delivered',0)}")
        self.add_text(self.ov_neural,f"dropped / evicted  {m.get('dropped',0)} / {m.get('evicted',0)}")
        self.add_text(self.ov_neural,f"errors  {m.get('errors',0)}")
        for lab,key in [("energy","energy"),("fatigue","fatigue"),("curiosity","curiosity"),("stress","stress"),("boredom","boredom"),("satisfaction","satisfaction")]:
            self.add_meter(self.ov_state,lab,state.get(key,0))
        vis=world.get("screen") or {}; aud=senses.get("audio") or {}
        self.add_text(self.ov_sense,"VISION   "+("ONLINE" if vis.get("captured") else "OFF"))
        self.add_text(self.ov_sense,"HEARING  "+("ONLINE" if not aud.get("error") else "DEGRADED"))
        self.add_text(self.ov_sense,"CAMERA   "+("PRESENT" if hw.get("camera_devices") else "NONE"))
        for k,c in list(comps.items())[:8]:
            self.add_text(self.ov_health,k+"  •  "+("OK" if c and not c.get("error_count") else "CHECK"))
        self.add_text(self.ov_flow,"SENSE  →  NERVOUS  →  CC  →  MOTOR  →  TOY",True)
        self.add_text(self.ov_flow,"latest  "+str(latest.get("source","—"))+" → "+str(latest.get("kind","—")))
        self.add_text(self.ov_flow,"status  "+("READY" if active else "STANDBY"))
        self.add_text(self.ov_flow,"free disk  %.1f GB"%(num(perf.get("disk_free_gai"))/1e9))

        # Neural layer
        nf=self.data.get("neural_fabric") or {}
        for p in [self.neural_overview,self.neural_topology,self.neural_lifecycle,self.neural_evidence]: self.clear_panel(p)
        self.add_text(self.neural_overview,"PHASE  "+str(nf.get("phase","—")),True)
        self.add_text(self.neural_overview,"GENERATION  "+str(nf.get("generation","—")))
        self.add_text(self.neural_overview,"STATUS  "+("ONLINE" if nf else "NO SNAPSHOT"))
        self.add_text(self.neural_overview,"physical sleep latched  "+str(nf.get("physical_sleep_latched","—")))
        self.add_text(self.neural_topology,"EDGES  "+str(nf.get("edges","—")),True)
        self.add_text(self.neural_topology,"connections / routes  "+str(nf.get("connections",nf.get("routes","—"))))
        self.add_text(self.neural_topology,"active paths  "+str(nf.get("active_paths",nf.get("active_edges","—"))))
        self.add_text(self.neural_topology,"fabric version  "+str(nf.get("version",nf.get("fabric_version","—"))))
        self.add_text(self.neural_lifecycle,"PHYSICAL SLEEP SESSIONS  "+str(nf.get("physical_sleep_sessions","—")),True)
        self.add_text(self.neural_lifecycle,"phase  "+str(nf.get("phase","—")))
        self.add_text(self.neural_lifecycle,"latched  "+str(nf.get("physical_sleep_latched","—")))
        self.add_text(self.neural_lifecycle,"wake / resume evidence  "+str(nf.get("resume_count",nf.get("wake_count","—"))))
        self.add_text(self.neural_evidence,"generation  "+str(nf.get("generation","—"))+"  •  edges  "+str(nf.get("edges","—")),True)
        self.add_text(self.neural_evidence,"This page exposes the neural fabric as a first-class diagnostic layer.")
        self.add_text(self.neural_evidence,"It is observational only; no neural state is changed here.")

        # Nervous
        for p in [self.neural_metrics,self.neural_events,self.neural_components]: self.clear_panel(p)
        self.add_text(self.neural_metrics,f"published  {m.get('published',0)}    delivered  {m.get('delivered',0)}",True)
        self.add_text(self.neural_metrics,f"dropped  {m.get('dropped',0)}    evicted  {m.get('evicted',0)}")
        self.add_text(self.neural_metrics,f"expired  {m.get('expired',0)}    gated  {m.get('gated',0)}")
        self.add_text(self.neural_metrics,f"errors  {m.get('errors',0)}")
        for e in self.events[:12]:
            self.add_text(self.neural_events,f"{e.get('source','?')} → {e.get('kind','?')}   [{e.get('priority','?')}]")
        for k,c in comps.items():
            self.add_text(self.neural_components,k+"  •  "+("OK" if c and not c.get("error_count") else "CHECK"))

        # Cognition
        for p in [self.cog_thought,self.cog_state,self.cog_needs,self.cog_history]: self.clear_panel(p)
        self.add_text(self.cog_thought,thought,True)
        self.add_text(self.cog_thought,"intention  "+str(intent.get("type","—")))
        self.add_text(self.cog_thought,"event  "+str(latest.get("kind","—")))
        self.add_text(self.cog_thought,"model  model-free V1")
        for lab,key in [("energy","energy"),("fatigue","fatigue"),("curiosity","curiosity"),("stress","stress"),("boredom","boredom"),("satisfaction","satisfaction")]: self.add_meter(self.cog_state,lab,state.get(key,0))
        for k,v in needs.items(): self.add_text(self.cog_needs,f"{k}  {num(v):.3f}")
        for e in (self.events[:10]): self.add_text(self.cog_history,f"{e.get('source','?')} → {e.get('kind','?')}")

        # Senses/body
        for p in [self.sense_vision,self.sense_hearing,self.sense_camera,self.sense_body,self.sense_motor,self.sense_attention]: self.clear_panel(p)
        self.add_text(self.sense_vision,"capture  "+str(vis.get("captured","—")),True)
        self.add_text(self.sense_vision,"resolution  "+str(vis.get("width","?"))+" × "+str(vis.get("height","?")))
        self.add_text(self.sense_vision,"gaze  "+str((vis.get("gaze") or {}).get("x","—"))+" / "+str((vis.get("gaze") or {}).get("y","—")))
        self.add_text(self.sense_vision,"change  "+str((vis.get("visual") or {}).get("structure_change","—")))
        self.add_text(self.sense_hearing,"signal  "+("available" if not aud.get("error") else str(aud.get("error"))),True)
        self.add_text(self.sense_hearing,"RMS  "+str(aud.get("rms",jread(AUDIO).get("rms","—"))))
        self.add_text(self.sense_hearing,"input state  "+str(aud.get("state","—")))
        self.add_text(self.sense_camera,"devices  "+str(hw.get("camera_devices",[])),True)
        self.add_text(self.sense_camera,"GPU  "+str(hw.get("nvidia","none")))
        self.add_text(self.sense_body,f"position  {prop.get('x','—')}, {prop.get('y','—')}",True)
        self.add_text(self.sense_body,"reason  "+str(prop.get("reason","—")))
        self.add_text(self.sense_motor,"action  "+str(motor.get("action","—")),True)
        self.add_text(self.sense_motor,"Δ  (%.1f, %.1f)"%(num(motor.get("dx")),num(motor.get("dy"))))
        self.add_text(self.sense_motor,"reason  "+str(motor.get("reason","—")))
        self.add_text(self.sense_attention,"tool  "+str(inter.get("tool","—")),True)
        self.add_text(self.sense_attention,"target  "+str(outputs.get("view",{}).get("target","—")))
        self.add_text(self.sense_attention,"gaze target  "+str((vis.get("visual") or {}).get("gaze",{}).get("target","none")))

        # Memory
        for p in [self.mem_work,self.mem_long,self.mem_deep,self.mem_flow]: self.clear_panel(p)
        wm=comps.get("working_memory",{}); mem=comps.get("memory",{})
        self.add_text(self.mem_work,"WORKING  •  "+("OK" if wm else "MISSING"),True)
        self.add_text(self.mem_work,"items  "+str((wm.get("detail") or {}).get("items","—")))
        self.add_text(self.mem_long,"LONG-TERM  •  "+("OK" if mem else "MISSING"),True)
        self.add_text(self.mem_long,"saved  "+str((mem.get("detail") or {}).get("saved","—")))
        self.add_text(self.mem_deep,"DEEP STORAGE  •  "+("AVAILABLE" if DEEP.exists() else "MISSING"),True)
        banks=list(DEEP.glob("bank-*.jsonl.gz")) if DEEP.exists() else []
        self.add_text(self.mem_deep,"banks  "+str(len(banks)))
        self.add_text(self.mem_flow,"working  →  candidate  →  validated  →  long-term  →  deep archive",True)
        self.add_text(self.mem_flow,"latest memory  "+str((mem.get("detail") or {}).get("memory_id","—")))
        self.add_text(self.mem_flow,"provenance + confidence + checksum")

        # Outputs
        for p in [self.out_windows,self.out_audio,self.out_motor,self.out_inter]: self.clear_panel(p)
        for k in ("view","thought","text","pixels"):
            s=outputs.get(k,{})
            self.add_text(self.out_windows,k+"  •  "+("VISIBLE" if s.get("visible",True) else "HIDDEN"),True)
        self.add_text(self.out_audio,"SPEAKER  •  "+("ACTIVE" if body.get("audio_active") else "IDLE"),True)
        self.add_text(self.out_audio,"emotion  "+str(body.get("emotion","idle")))
        self.add_text(self.out_audio,"frequency  "+str(body.get("frequency","—"))+" Hz")
        self.add_text(self.out_audio,"RMS / peak  %.4f / %.4f"%(num(body.get("rms")),num(body.get("peak"))))
        self.add_text(self.out_motor,"command  "+str(motor.get("action","—")),True)
        self.add_text(self.out_motor,"primitive  "+str(comps.get("motor_action",{}).get("detail",{}).get("last_primitive","—")))
        self.add_text(self.out_motor,"body  "+str(body.get("action","—")))
        self.add_text(self.out_inter,"hand target  "+str(inter.get("tool","—")),True)
        self.add_text(self.out_inter,"age  "+str(round(age(inter.get("timestamp")) or 0,1))+" s")
        self.add_text(self.out_inter,"the diagnostic is external")

        # Lab
        for p in [self.lab_session,self.lab_event,self.lab_resources,self.lab_archive]: self.clear_panel(p)
        speed=num(jread(SPEED).get("multiplier"),1)
        self.add_text(self.lab_session,"G.A.I.  •  "+("ACTIVE" if active else "OFF"),True)
        self.add_text(self.lab_session,f"brain base 0.50 FPS  ×{speed:g}")
        self.add_text(self.lab_session,"policy  model-free V1")
        self.add_text(self.lab_session,"diagnostic  external")
        self.add_text(self.lab_event,str(latest.get("source","—"))+" → "+str(latest.get("kind","—")),True)
        self.add_text(self.lab_event,"event id  "+str(latest.get("event_id","—")))
        self.add_text(self.lab_event,"priority  "+str(latest.get("priority","—")))
        self.add_text(self.lab_resources,"RAM available  %.1f GB"%(num(perf.get("memory_available"))/1e9),True)
        self.add_text(self.lab_resources,"CPU load  %.2f"%num(perf.get("load_1m")))
        self.add_text(self.lab_resources,"CPU cores  "+str(perf.get("cpu_count","—")))
        self.add_text(self.lab_resources,"disk free  %.1f GB"%(num(perf.get("disk_free_gai"))/1e9))
        self.add_text(self.lab_archive,"faults  "+str(m.get("errors",0)),True)
        self.add_text(self.lab_archive,"launcher log  "+("present" if LOG.exists() else "missing"))
        self.add_text(self.lab_archive,"status  "+("READY" if active else "STANDBY"))
        self.add_text(self.lab_archive,"archive-safe: previous diagnostic retained")

    def suggest(self, command):
        payload={"id":str(uuid.uuid4()),"command":command,"source":"diagnostic","timestamp":time.time()}
        COMMAND.parent.mkdir(parents=True,exist_ok=True)
        COMMAND.write_text(json.dumps(payload,indent=2))
        self.result_label.setText(f"Suggested: {command}. Waiting for G.A.I. to evaluate…")
        self.result_label.setStyleSheet(f"color:{CYAN};")

    def _load_speed(self):
        value=num(jread(SPEED).get("multiplier"),1.0)
        idx=min(range(len(SPEEDS)),key=lambda i:abs(SPEEDS[i]-value))
        self.speed_box.blockSignals(True); self.speed_box.setCurrentIndex(idx); self.speed_box.blockSignals(False)

    def set_speed(self,index):
        value=SPEEDS[max(0,min(len(SPEEDS)-1,int(index)))]
        SPEED.parent.mkdir(parents=True,exist_ok=True)
        SPEED.write_text(json.dumps({"multiplier":value,"timestamp":time.time(),"source":"diagnostic"}))

    def show_page(self,index):
        self.current_page=index
        self.stack.setCurrentIndex(index)
        for i,b in enumerate(self.nav):
            b.setChecked(i==index)

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.show_page(max(0,self.current_page-1))
        elif event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.show_page(min(len(self.nav)-1,self.current_page+1))
        elif event.key()==Qt.Key_1: self.show_page(0)
        elif event.key()==Qt.Key_2: self.show_page(1)
        elif event.key()==Qt.Key_3: self.show_page(2)
        elif event.key()==Qt.Key_4: self.show_page(3)
        elif event.key()==Qt.Key_5: self.show_page(4)
        elif event.key()==Qt.Key_6: self.show_page(5)
        elif event.key()==Qt.Key_7: self.show_page(6)
        elif event.key()==Qt.Key_8: self.show_page(7)
        else: super().keyPressEvent(event)

def main():
    lock_path = STATE / 'diagnostic.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open('w')
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    app=QApplication([])
    apply(app)
    d=Diagnostic()
    d.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())
