from __future__ import annotations
import json, os, sys
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QSize, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QPixmap, QFont
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
from gui.theme import apply, MONO
from core.habitat import DigitalHabitat

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'; CREATIVE=ROOT/'creative'; CTRL=STATE/'output_windows.json'; PID=STATE/'output_windows.pid'

def read(p):
    try: return json.loads(p.read_text())
    except Exception: return {}

def latest(folder,suffixes):
    try:
        xs=[p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in suffixes]
        return max(xs,key=lambda p:p.stat().st_mtime) if xs else None
    except Exception: return None

def clamp(v,a=0,b=1):
    try: v=float(v)
    except Exception: v=0
    return max(a,min(b,v))

class ToyWindow(QWidget):
    def __init__(self,kind,title,subtitle,size):
        super().__init__(); self.kind=kind
        self.setWindowTitle(f'G.A.I. • {title}'); self.setWindowFlags(Qt.Window); self.resize(*size); self.setMinimumSize(300,220)
        root=QVBoxLayout(self); root.setContentsMargins(14,14,14,14); root.setSpacing(10)
        head=QHBoxLayout(); badge=QLabel(title.upper()); badge.setStyleSheet('QLabel{color:#a8c7d5;font-weight:700;font-size:10px;padding:5px 8px;border:1px solid #334650;background:#070e14;}'); head.addWidget(badge)
        sub=QLabel(subtitle); sub.setStyleSheet('color:#7890a0;font-size:11px;'); head.addWidget(sub); head.addStretch(); root.addLayout(head)
        self.content=QLabel(); self.content.setAlignment(Qt.AlignCenter); self.content.setWordWrap(True); self.content.setStyleSheet('QLabel{background:#08131d;border:1px solid #1e4052;border-radius:16px;padding:12px;}'); root.addWidget(self.content,1)
        self.editor=None
        if kind=='text':
            self.content.hide(); self.editor=QTextEdit(); self.editor.setStyleSheet('QTextEdit{background:#08131d;color:#dce7f5;border:1px solid #1e4052;border-radius:16px;padding:12px;font-size:14px;}'); root.addWidget(self.editor,1)
        foot=QLabel('persistent organ • controlled by G.A.I.'); foot.setAlignment(Qt.AlignCenter); foot.setStyleSheet('color:#4f7181;font-size:9px;'); root.addWidget(foot)
        self.refresh()

    def refresh(self):
        runtime=read(STATE/'runtime.json'); v1=runtime.get('v1') or {}; selected=(v1.get('attention') or {}).get('selected') or {}
        if self.kind=='habitat': self.render_habitat()
        elif self.kind=='view': self.render_view(selected)
        elif self.kind=='state': self.render_state(runtime,selected)
        elif self.kind=='text': self.render_text()
        elif self.kind=='pixels': self.render_pixels()
        return
        if self.kind=='habitat': self.render_habitat()
        elif self.kind=='view': self.render_view(selected)
        elif self.kind=='state': self.render_state(runtime,selected)
        elif self.kind=='text': self.render_text()
        elif self.kind=='pixels': self.render_pixels()

    def render_habitat(self):
        h=DigitalHabitat(); objs=h.objects(); lines=['DIGITAL HABITAT','',f'OBJECTS  {len(objs)}','']
        for o in objs:
            mark='●' if o.get('state') not in ('quiet','off','ready','stable') else '○'
            lines.append(f"{mark} {o.get('id','object'):16} {o.get('state','?'):10}  changes={o.get('changes',0)}")
        last=(h.state.get('last_event') or {})
        if last: lines += ['',f"LAST  {last.get('kind')} → {last.get('object')}"]
        self.content.setText('\n'.join(lines)); self.content.setFont(QFont('DejaVu Sans Mono',10))

    def render_view(self,selected):
        focus=read(STATE/'sight_focus.json')
        mode='out' if str(focus.get('mode','out'))=='out' else 'in'
        sources=(STATE/'camera_stream.jpg',) if mode=='out' else (STATE/'screen_stream.jpg',)
        im=None
        for path in sources:
            q=QImage(str(path))
            if not q.isNull(): im=q; break
        if im is None: self.content.setText('No visual field yet.'); return
        im=im.scaled(self.content.size()-QSize(20,20),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        f=read(STATE/'sight_focus.json'); x=clamp(f.get('x',.5)); y=clamp(f.get('y',.5)); rr=max(12,int(.12*min(im.width(),im.height())))
        p=QPainter(im); p.setRenderHint(QPainter.Antialiasing); p.setPen(QPen(QColor(112,217,255,210),2)); px=int(x*im.width()); py=int(y*im.height()); p.drawEllipse(QPointF(px,py),rr,rr); p.drawLine(px-7,py,px+7,py); p.drawLine(px,py-7,px,py+7); p.end()
        self.content.setPixmap(QPixmap.fromImage(im)); self.content.setToolTip(str(selected.get('target','visual field')))

    def render_state(self,runtime,selected):
        s=runtime.get('state') or {}; intention=((runtime.get('v1') or {}).get('last_decision') or {}).get('intention') or {}
        rows=[('ENERGY',s.get('energy',0)),('CURIOSITY',s.get('curiosity',0)),('BOREDOM',s.get('boredom',0)),('STRESS',s.get('stress',0)),('SATISFACTION',s.get('satisfaction',0))]
        text=''.join(f'{k:<12} {clamp(v):.2f}\n' for k,v in rows)+f"\nATTENTION  {selected.get('modality','none')} / {selected.get('target','nothing')}\nACTION     {intention.get('type','wait')}\nSALIENCE   {float(selected.get('salience',0)):.2f}"
        self.content.setText(text); self.content.setFont(QFont('DejaVu Sans Mono',11))

    def render_text(self):
        if self.editor is None or self.editor.hasFocus(): return
        p=latest(CREATIVE/'text',{'.txt','.md'}); self.editor.setPlainText(p.read_text()[:10000] if p else '')

    def render_pixels(self):
        p=latest(CREATIVE/'images',{'.png','.jpg','.jpeg','.webp','.svg'}) or latest(CREATIVE/'paint',{'.png','.jpg','.jpeg','.webp','.svg'})
        if not p: self.content.setText('No image yet.\n\nThe pixels organ is ready.'); return
        if p.suffix.lower()=='.svg':
            try:
                from PySide6.QtSvg import QSvgRenderer
                pm=QPixmap(self.content.size()-QSize(20,20)); pm.fill(QColor('#08131d')); q=QPainter(pm); QSvgRenderer(str(p)).render(q); q.end(); self.content.setPixmap(pm)
            except Exception: self.content.setText(p.name)
        else: self.content.setPixmap(QPixmap(str(p)).scaled(self.content.size()-QSize(20,20),Qt.KeepAspectRatio,Qt.SmoothTransformation))

class ToySuite:
    def __init__(self):
        self.app=QApplication(sys.argv); self.app.setApplicationName('G.A.I. Toys'); apply(self.app); PID.write_text(str(os.getpid()))
        self.windows={'habitat':ToyWindow('habitat','HABITAT','persistent digital environment',(520,430)),'view':ToyWindow('view','VIEW','visual field + gaze',(560,390)),'state':ToyWindow('state','STATE','internal condition + attention',(420,360)),'text':ToyWindow('text','TEXT','persistent writing surface',(560,430)),'pixels':ToyWindow('pixels','PIXELS','persistent image surface',(560,460))}
        self.defaults={'habitat':{'visible':True,'x':80,'y':120,'opacity':.96},'view':{'visible':False,'x':30,'y':30,'opacity':.94},'state':{'visible':False,'x':610,'y':30,'opacity':.94},'text':{'visible':False,'x':30,'y':445,'opacity':.94},'pixels':{'visible':False,'x':610,'y':420,'opacity':.94}}
        self.timer=QTimer(); self.timer.timeout.connect(self.refresh); self.timer.start(350); self.refresh()

    def refresh(self):
        cfg=read(CTRL)
        for k,w in self.windows.items():
            spec={**self.defaults[k],**cfg.get(k,{})}
            if spec.get('x') is not None and spec.get('y') is not None: w.move(int(spec['x']),int(spec['y']))
            try: w.setWindowOpacity(clamp(spec.get('opacity',.94),.25,1))
            except Exception: pass
            if bool(spec.get('visible',False)) != w.isVisible(): w.setVisible(bool(spec.get('visible',False)))
            w.refresh()

    def run(self):
        try: return self.app.exec()
        finally:
            try: PID.unlink()
            except FileNotFoundError: pass

if __name__=='__main__': raise SystemExit(ToySuite().run())
