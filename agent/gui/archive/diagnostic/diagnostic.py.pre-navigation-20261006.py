from __future__ import annotations
import json, os, time, math, shutil, subprocess
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget, QComboBox
from gui.theme import apply

ROOT=Path("/mnt/gai")
STATE=ROOT/"state"
RUNTIME=STATE/"runtime.json"
EVENT_LOG=STATE/"events.jsonl"
ACTIVE=STATE/"gai_active.json"
PROPRIO=STATE/"proprioception.json"
MOTOR=STATE/"motor_output.json"
BODY=STATE/"body_output.json"
INTERACTION=STATE/"toy_interaction.json"
OUTPUTS=STATE/"output_windows.json"
AUDIO=STATE/"audio_input.json"
DEEP=ROOT/"storage/simulated_hdd/deep_storage"
LOG=ROOT/"logs/launcher.log"
SPEED=STATE/"simulation_speed.json"
SPEEDS=(0.1,0.25,0.5,1.0,2.0,5.0,10.0)

def jread(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

def num(v,d=0.0):
    try: return float(v)
    except Exception: return d

def age(ts):
    return max(0,time.time()-num(ts,time.time())) if ts else None

class Diagnostic(QWidget):
    """External diagnostic instrument. It observes G.A.I.; it is not an organ."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("G.A.I. Diagnostic Instrument")
        self.setWindowFlags(Qt.Window)
        self.resize(1220,820)
        self.setMinimumSize(980,680)
        self.font=QFont("DejaVu Sans",10)
        self.mono=QFont("DejaVu Sans Mono",9)
        self.data={}
        self.events=[]
        self.speed_box=QComboBox(self)
        self.speed_box.addItems([f"×{x:g}" for x in SPEEDS])
        self.speed_box.currentIndexChanged.connect(self.set_speed)
        self.speed_box.setStyleSheet("QComboBox{background:#0b1722;color:#9eeaff;border:1px solid #24566b;border-radius:8px;padding:5px 10px;font-weight:700;} QComboBox QAbstractItemView{background:#0b1722;color:#dce7f5;}")
        self._load_speed()
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(500)
        self.refresh()

    def _load_speed(self):
        try:
            obj=jread(SPEED)
            value=float(obj.get("multiplier",1.0))
        except Exception:
            value=1.0
        idx=min(range(len(SPEEDS)), key=lambda i: abs(SPEEDS[i]-value))
        self.speed_box.blockSignals(True)
        self.speed_box.setCurrentIndex(idx)
        self.speed_box.blockSignals(False)

    def set_speed(self, index):
        value=SPEEDS[max(0,min(len(SPEEDS)-1,int(index)))]
        SPEED.parent.mkdir(parents=True, exist_ok=True)
        SPEED.write_text(json.dumps({"multiplier":value,"timestamp":time.time(),"source":"diagnostic"}))
        self.update()

    def resizeEvent(self,event):
        self.speed_box.setGeometry(max(780,self.width()-155), 8, 140, 34)
        super().resizeEvent(event)

    def keyPressEvent(self,event):
        key=event.key()
        idx=self.speed_box.currentIndex()
        if key==Qt.Key_Left and idx>0:
            self.speed_box.setCurrentIndex(idx-1)
        elif key==Qt.Key_Right and idx<len(SPEEDS)-1:
            self.speed_box.setCurrentIndex(idx+1)
        elif key==Qt.Key_0:
            self.speed_box.setCurrentIndex(3)
        else:
            super().keyPressEvent(event)

    def refresh(self):
        self._load_speed()
        self.data=jread(RUNTIME)
        self.events=self._events()
        self.update()

    def _events(self):
        out=[]
        try:
            for line in EVENT_LOG.read_text().splitlines()[-80:]:
                try: out.append(json.loads(line))
                except Exception: pass
        except Exception:
            pass
        latest=((self.data.get("nervous") or {}).get("latest_events") or [])
        if latest:
            # Runtime snapshots are authoritative when the event log is absent.
            known={(e.get("event_id"),e.get("timestamp")) for e in out}
            out += [e for e in latest if (e.get("event_id"),e.get("timestamp")) not in known]
        return sorted(out,key=lambda e:num(e.get("timestamp")),reverse=True)[:18]

    def txt(self,painter,x,y,s,size=10,bright=True):
        painter.setFont(QFont(self.font.family(),size,QFont.Bold if bright else QFont.Normal))
        painter.setPen(QColor(225,235,245,235) if bright else QColor(155,170,185,220))
        painter.drawText(int(x),int(y),str(s))

    def panel(self,p,x,y,w,h,title):
        p.setPen(QPen(QColor(80,105,130,150),1))
        p.setBrush(QBrush(QColor(7,12,19,235)))
        p.drawRoundedRect(QRectF(x,y,w,h),12,12)
        self.txt(p,x+12,y+22,title.upper(),10,True)

    def bar(self,p,x,y,w,value,label):
        value=max(0,min(1,num(value)))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(30,43,55,220)))
        p.drawRoundedRect(QRectF(x,y,w,8),4,4)
        p.setBrush(QBrush(QColor(80,210,235,210)))
        p.drawRoundedRect(QRectF(x,y,w*value,8),4,4)
        self.txt(p,x,y-4,label,9,False)
        self.txt(p,x+w+7,y+7,f"{value:.2f}",9,False)

    def status(self,p,x,y,label,ok=True,detail=""):
        c=QColor(75,220,135) if ok else QColor(255,85,95)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(c)); p.drawEllipse(QRectF(x,y-9,8,8))
        self.txt(p,x+14,y,label,9,True)
        if detail: self.txt(p,x+14,y+15,detail,8,False)

    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(),QColor(3,7,12))
        w,h=self.width(),self.height()
        active=bool(jread(ACTIVE).get("active"))
        state=self.data.get("state") or {}
        nervous=self.data.get("nervous") or {}
        comps=nervous.get("components") or {}
        senses=self.data.get("world",{}).get("last_observation",{}).get("senses") or {}
        world=self.data.get("world",{}).get("last_observation") or {}
        thoughts=self.data.get("thoughts") or {}
        drives=self.data.get("drives") or {}
        needs=self.data.get("core_needs") or {}
        perf=world.get("system") or {}
        hw=world.get("hardware") or {}
        latest=self.events[0] if self.events else {}
        intent=(latest.get("payload") or {}).get("intention") or {}
        motor=jread(MOTOR); prop=jread(PROPRIO); body=jread(BODY); inter=jread(INTERACTION)
        outputs=jread(OUTPUTS)

        # Header / health
        self.txt(p,22,28,"G.A.I. DIAGNOSTIC INSTRUMENT",15,True)
        self.txt(p,22,49,"external observer • does not participate in cognition",9,False)
        self.status(p,330,27,"RUNNING" if active else "OFF",active,
                    "phase: "+str((self.data.get("sensory") or {}).get("phase","unknown")))
        self.txt(p,510,28,f"events {nervous.get('metrics',{}).get('delivered',0)} delivered",9,False)
        self.txt(p,690,28,f"workers {needs.get('processing',0):.2f} load",9,False)
        self.txt(p,900,28,f"free disk {perf.get('disk_free_gai',0)/1e9:.1f} GB",9,False)

        # 1 Central Circuit
        self.panel(p,15,65,285,210,"1 • CENTRAL CIRCUIT")
        cc=comps.get("cognitive_core",{})
        self.status(p,30,95,"healthy" if cc and not cc.get("error_count") else "degraded",bool(cc) and not cc.get("error_count"),"cycle "+str((cc.get("detail") or {}).get("cycle","—")))
        self.txt(p,30,125,"last thought:",9,False)
        thought=((thoughts.get("recent") or [{}])[-1].get("text") or latest.get("payload",{}).get("thought","—"))
        self.txt(p,30,147,thought[:42],9,True)
        self.txt(p,30,166,thought[42:84],9,True)
        self.txt(p,30,190,"intention: "+str(intent.get("type","—")),9,False)
        self.txt(p,30,209,"confidence: "+str((latest.get("payload") or {}).get("confidence","—")),9,False)
        self.txt(p,30,228,"cognition: model-free V1",9,False)
        self.txt(p,30,247,"wake/event driven",9,False)

        # 2 Nervous system
        self.panel(p,310,65,285,210,"2 • NERVOUS SYSTEM")
        m=nervous.get("metrics") or {}
        self.status(p,325,95,"transport healthy",m.get("errors",0)==0,m.get("errors",0))
        self.txt(p,325,120,f"published {m.get('published',0)}",9,False)
        self.txt(p,325,139,f"delivered {m.get('delivered',0)}",9,False)
        self.txt(p,325,158,f"dropped {m.get('dropped',0)}  evicted {m.get('evicted',0)}",9,False)
        self.txt(p,325,177,f"expired {m.get('expired',0)}  gated {m.get('gated',0)}",9,False)
        self.txt(p,325,196,"latest events:",9,False)
        for i,e in enumerate(self.events[:3]):
            self.txt(p,325,214+i*16,f"{e.get('source','?')} → {e.get('kind','?')}"[:34],8,False)

        # 3 Internal state
        self.panel(p,605,65,285,210,"3 • INTERNAL STATE")
        for i,(lab,key) in enumerate([("energy","energy"),("fatigue","fatigue"),("curiosity","curiosity"),("stress","stress"),("boredom","boredom"),("satisfaction","satisfaction")]):
            self.bar(p,620,98+i*27,190,state.get(key,0),lab)

        # 4 Sensory organs
        self.panel(p,900,65,305,210,"4 • SENSORY ORGANS")
        vis=world.get("screen") or {}; aud=senses.get("audio") or {}
        self.status(p,915,96,"VISION",bool(vis.get("captured")),str(vis.get("width","?"))+"×"+str(vis.get("height","?")))
        self.txt(p,915,119,"gaze "+str((vis.get("gaze") or {}).get("x","—"))+" / "+str((vis.get("gaze") or {}).get("y","—")),8,False)
        self.status(p,915,145,"HEARING",not aud.get("error"),str(aud.get("error","signal available")))
        self.txt(p,915,168,"rms "+str(aud.get("rms",jread(AUDIO).get("rms","—"))),8,False)
        self.status(p,915,194,"CAMERA",bool(hw.get("camera_devices")),str(hw.get("camera_devices",[]))[:28])
        self.txt(p,915,218,"visual change "+str((vis.get("visual") or {}).get("structure_change","—")),8,False)
        self.txt(p,915,240,"gaze target "+str((vis.get("visual") or {}).get("gaze",{}).get("target","none")),8,False)

        # 5 Motor
        self.panel(p,15,290,285,190,"5 • MOTOR SYSTEM")
        self.status(p,30,320,"MOTOR CENTRE",bool(comps.get("motor_action")), "state "+str(comps.get("motor_action",{}).get("state","—")))
        self.txt(p,30,345,"goal → "+str(intent.get("type","—")),9,False)
        self.txt(p,30,363,"command → "+str(motor.get("action","—")),9,False)
        self.txt(p,30,381,f"Δ ({num(motor.get('dx')):.1f}, {num(motor.get('dy')):.1f})",9,False)
        self.txt(p,30,399,"reason → "+str(motor.get("reason","—")),9,False)
        self.txt(p,30,417,"primitive → "+str(comps.get("motor_action",{}).get("detail",{}).get("last_primitive","—")),9,False)
        self.txt(p,30,440,"proprio → "+str(prop.get("reason","—")),8,False)
        self.txt(p,30,457,f"body @ {prop.get('x','—')},{prop.get('y','—')}",8,False)

        # 6 Toys / organs
        self.panel(p,310,290,285,190,"6 • TOY / OUTPUT ORGANS")
        for i,k in enumerate(("view","thought","text","pixels")):
            s=outputs.get(k,{})
            using=inter.get("tool")==k and age(inter.get("timestamp"))<3
            self.status(p,325,322+i*32,k, bool(s.get("visible",True)), "USING" if using else "idle")
        if inter: self.txt(p,325,458,"hand target → "+str(inter.get("tool","—")),8,False)

        # 7 Audio output
        self.panel(p,605,290,285,190,"7 • AUDIO OUTPUT")
        self.status(p,620,322,"SPEAKER",bool(body.get("audio_active")),body.get("emotion","idle"))
        self.txt(p,620,347,"frequency "+str(body.get("frequency","—"))+" Hz",9,False)
        self.txt(p,620,366,"RMS "+str(round(num(body.get("rms")),4))+"  peak "+str(round(num(body.get("peak")),4)),9,False)
        self.txt(p,620,385,"last text "+str(body.get("text","—"))[:28],8,False)
        self.txt(p,620,410,"action "+str(body.get("action","—")),8,False)
        self.bar(p,620,447,190,num(body.get("rms"))*8,"output level")

        # 8 Organ health
        self.panel(p,900,290,305,190,"8 • ORGAN HEALTH")
        health=[
            ("kernel",comps.get("kernel")),("perception",comps.get("perception")),
            ("motivation",comps.get("motivation")),("memory",comps.get("memory")),
            ("working_memory",comps.get("working_memory")),("motor_action",comps.get("motor_action")),
            ("cognitive_core",comps.get("cognitive_core")),("supervisor",comps.get("supervisor"))]
        for i,(k,c) in enumerate(health):
            col=i%2; row=i//2
            self.status(p,915+col*145,322+row*37,k,bool(c) and not c.get("error_count"),"OK" if c else "missing")

        # 9 Memory
        self.panel(p,15,495,285,300,"9 • MEMORY")
        wm=comps.get("working_memory",{}); mem=comps.get("memory",{})
        self.status(p,30,527,"WORKING",bool(wm),"items "+str((wm.get("detail") or {}).get("items","—")))
        self.status(p,30,563,"LONG-TERM",bool(mem),"saved "+str((mem.get("detail") or {}).get("saved","—")))
        self.status(p,30,599,"DEEP STORAGE",DEEP.exists(),"bank dir")
        if DEEP.exists():
            try:
                banks=list(DEEP.glob("bank-*.jsonl.gz"))
                self.txt(p,30,620,f"banks {len(banks)}",8,False)
            except Exception: pass
        self.txt(p,30,652,"flow",9,True)
        self.txt(p,30,672,"working → candidate → validated",8,False)
        self.txt(p,30,689,"→ long-term → deep archive",8,False)
        self.txt(p,30,721,"latest memory: "+str((mem.get("detail") or {}).get("memory_id","—")),8,False)
        self.txt(p,30,741,"provenance + confidence + checksum",8,False)

        # 10 Metabolism/resources
        self.panel(p,310,495,285,300,"10 • METABOLISM / RESOURCES")
        total=num(perf.get("memory_total")); avail=num(perf.get("memory_available"))
        ram=(1-avail/total) if total else 0
        self.bar(p,325,530,190,ram,"RAM used")
        load=num(perf.get("load_1m")); cpu=max(0,min(1,load/max(1,num(perf.get("cpu_count"),1))))
        self.bar(p,325,572,190,cpu,"CPU load")
        self.txt(p,325,610,f"CPU cores {perf.get('cpu_count','—')}",9,False)
        self.txt(p,325,629,f"load 1m {load:.2f}",9,False)
        self.txt(p,325,648,f"free RAM {avail/1e9:.1f} GB",9,False)
        self.txt(p,325,667,f"GPU {str(hw.get('nvidia','none'))[:32]}",8,False)
        self.txt(p,325,690,"processing need %.3f"%num(needs.get("processing")),8,False)
        self.txt(p,325,709,"power budget %.3f"%num(needs.get("power")),8,False)
        self.txt(p,325,728,"energy %.3f"%num(state.get("energy")),8,False)
        self.txt(p,325,747,"metabolic load = compute + activity",8,False)

        # Event flow / experiment footer
        self.panel(p,605,495,600,300,"LIVE ORGANISM FLOW / DIAGNOSTIC EVIDENCE")
        nodes=[("SENSE",660,555),("NERVOUS",800,555),("CC",940,555),("MOTOR",1080,555),("TOY",1140,665)]
        for i,(name,x,y) in enumerate(nodes):
            p.setPen(QPen(QColor(80,200,225,180),2)); p.setBrush(QBrush(QColor(10,25,35,240)))
            p.drawEllipse(QRectF(x-45,y-18,90,36))
            self.txt(p,x-30,y+5,name,8,True)
            if i<len(nodes)-1:
                nx=nodes[i+1][1]-45; p.drawLine(QPointF(x+45,y),QPointF(nx,nodes[i+1][2]))
        if latest:
            self.txt(p,625,625,"LATEST EVENT",9,True)
            self.txt(p,625,644,f"{latest.get('source','?')} → {latest.get('kind','?')}",9,False)
            self.txt(p,625,663,"id "+str(latest.get("event_id","—"))[:22],8,False)
            self.txt(p,625,682,"priority "+str(latest.get("priority","—"))+"  confidence "+str(latest.get("confidence","—")),8,False)
        self.txt(p,625,713,"EVENT BUFFER",9,True)
        for i,e in enumerate(self.events[:4]):
            self.txt(p,625,733+i*14,(str(e.get("kind","?"))+"  "+str(e.get("source","?")))[:48],8,False)
        self.txt(p,895,625,"EXPERIMENT / SESSION",9,True)
        speed=num(jread(SPEED).get("multiplier"),1.0)
        self.txt(p,895,645,"G.A.I. "+("ACTIVE" if active else "OFF"),9,False)
        self.txt(p,895,664,f"brain base 0.50 FPS  ×{speed:g}",9,True)
        self.txt(p,895,683,"policy: model-free V1 • language model off",8,False)
        self.txt(p,895,702,"diagnostic process: external",8,False)
        self.txt(p,895,720,"launcher log: "+("present" if LOG.exists() else "missing"),8,False)
        self.txt(p,895,738,"faults: "+str(m.get("errors",0)),8,False)
        self.txt(p,895,754,"status: "+("READY" if active else "STANDBY"),9,True)
        p.end()

def main():
    app=QApplication([]); apply(app)
    d=Diagnostic(); d.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())
