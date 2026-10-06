from __future__ import annotations
import json, math, time
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QBrush, QColor, QRadialGradient, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget
from perception.sight_focus import read as read_focus

ROOT=Path('/mnt/gai'); STATE=ROOT/'state/runtime.json'; MOTOR=ROOT/'state/motor_output.json'
PROPRIO=ROOT/'state/proprioception.json'; HANDS=ROOT/'state/hands.json'; FOCUS_INFO=ROOT/'state/focus_bubble.json'

def read_json(path):
    try: return json.loads(path.read_text())
    except Exception: return {}

def clamp(v,lo=0.0,hi=1.0):
    try: v=float(v)
    except Exception: v=0.0
    return max(lo,min(hi,v))

class Bubble(QWidget):
    """1960s computer-graphics phenotype: simple vector sphere, expressive face, no HUD."""
    AMBER=QColor(244,194,104)
    CREAM=QColor(255,226,166)
    DARK=QColor(18,15,10)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('G.A.I.')
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Window|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground,True)
        self.setAttribute(Qt.WA_ShowWithoutActivating,True)
        self.resize(270,270); self.move(50,50)
        self._drag_offset=None; self._manual_until=0.0; self._motor_stamp=None; self._render_tick=-1
        self.face_state={}

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self._manual_until=time.monotonic()+4.0
            self._drag_offset=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
        elif event.button()==Qt.RightButton: self.close()

    def mouseMoveEvent(self,event):
        if self._drag_offset is not None and event.buttons()&Qt.LeftButton:
            self.move(event.globalPosition().toPoint()-self._drag_offset); self._write_proprio('manual_drag')

    def mouseReleaseEvent(self,event): self._drag_offset=None

    def _write_proprio(self,reason):
        try:
            s=QApplication.primaryScreen().availableGeometry()
            PROPRIO.write_text(json.dumps({'timestamp':time.time(),'x':self.x(),'y':self.y(),'width':self.width(),'height':self.height(),
                'screen_width':s.width(),'screen_height':s.height(),'screen_center_x':s.center().x(),'screen_center_y':s.center().y(),'reason':reason},separators=(',',':')))
        except Exception: pass

    def _apply_motor(self):
        if time.monotonic()<self._manual_until: return
        motor=read_json(MOTOR)
        if motor.get('action')!='move' or motor.get('timestamp')==self._motor_stamp: return
        try:
            s=QApplication.primaryScreen().availableGeometry()
            dx=max(-500.0,min(500.0,float(motor.get('dx',0)))); dy=max(-300.0,min(300.0,float(motor.get('dy',0))))
            margin=18
            x=max(s.left()+margin,min(self.x()+dx,s.right()-self.width()-margin))
            y=max(s.top()+margin,min(self.y()+dy,s.bottom()-self.height()-margin))
            self.move(int(x),int(y)); self._write_proprio('motor_command_applied'); self._motor_stamp=motor.get('timestamp')
        except Exception: pass

    def _dot_field(self,p,cx,cy,r,phase,brightness):
        # Coarse halftone: the visual language of early computer graphics.
        p.save(); p.setClipRect(0,0,self.width(),self.height())
        step=9
        for yy in range(int(cy-r*.82),int(cy+r*.82),step):
            for xx in range(int(cx-r*.82),int(cx+r*.82),step):
                dx=xx-cx; dy=yy-cy; d=math.hypot(dx,dy)
                if d<r*.88:
                    edge=1-d/r
                    if edge>0.10:
                        a=int(8+28*edge*brightness)
                        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,218,150,a)))
                        p.drawEllipse(QPointF(xx+(phase%2),yy),1.0+edge*1.2,1.0+edge*1.2)
        p.restore()

    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); cx,cy=w/2,h/2+3; r=min(w,h)*.405
        tick=self.face_state.get('tick',{}) or {}
        idx=int(tick.get('tick_index',0) or 0); fps=max(.1,float(tick.get('target_fps',1) or 1)); t=idx/fps
        a=self.face_state.get('appearance') or {}
        v1=self.face_state.get('v1') or {}; decision=v1.get('last_decision') or {}; intention=decision.get('intention') or {}
        action=str(intention.get('type','wait')).lower()
        selected=(v1.get('attention') or {}).get('selected') or {}
        salience=clamp(selected.get('salience',0))
        focus=read_focus(); mode=focus.get('mode','out'); fx=clamp(focus.get('x',.5)); fy=clamp(focus.get('y',.5))
        finfo=read_json(FOCUS_INFO); dist=float(finfo.get('distance_px',1000) or 1000)
        proximity=1/(1+dist/220)
        curiosity=clamp(a.get('curiosity',.5)); satisfaction=clamp(a.get('satisfaction',.5))
        fear=clamp(a.get('fear',0)); stress=clamp(a.get('stress',0)); fatigue=clamp(a.get('fatigue',0))
        boredom=clamp(a.get('boredom',0)); happiness=clamp(a.get('happiness',0),-1,1)
        brightness=clamp(.45+.30*salience+.18*satisfaction-.12*fatigue)
        if a.get('phase')=='dream': brightness*=.55
        pulse=.5+.5*math.sin(t*2*math.pi*(.45+1.1*curiosity))
        if action=='vocalize': pulse=.5+.5*math.sin(t*2*math.pi*2.2)

        # Ground reflection and outer silhouette.
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(244,194,104,18+int(15*pulse))))
        p.drawEllipse(QPointF(cx,cy+r*1.02),r*.62,r*.10)

        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(244,194,104,22+int(20*brightness))))
        p.drawEllipse(QPointF(cx,cy),r*1.10,r*1.10)

        # Glass body: restrained monochrome radial shading.
        body=QRadialGradient(QPointF(cx-r*.28,cy-r*.32),r*1.15)
        body.setColorAt(0,QColor(255,229,174,55+int(55*brightness)))
        body.setColorAt(.48,QColor(65,53,34,235))
        body.setColorAt(1,QColor(8,9,9,250))
        p.setPen(Qt.NoPen); p.setBrush(QBrush(body)); p.drawEllipse(QPointF(cx,cy),r,r)

        # Concentric vector contours.
        p.setBrush(Qt.NoBrush)
        for frac,alpha in ((.92,52),(.78,32),(.62,22)):
            p.setPen(QPen(QColor(244,194,104,alpha+int(25*brightness)),.8))
            p.drawEllipse(QPointF(cx,cy),r*frac,r*frac*.985)

        # Halftone texture.
        self._dot_field(p,cx,cy,r,idx,brightness)

        # Highlight arcs / retro reflection.
        p.setPen(QPen(QColor(255,226,166,155+int(60*brightness)),2.0))
        arc_rect=QRectF(cx-r*.88,cy-r*.88,r*1.76,r*1.76)
        p.drawArc(arc_rect,35*16,82*16)
        p.setPen(QPen(QColor(244,194,104,80),1.0))
        p.drawArc(arc_rect,150*16,48*16)

        # Two tiny satellite bubbles: identity + low-key activity indicator.
        activity=.35+.65*max(salience,pulse if action=='vocalize' else 0)
        sr=r*(.055+.018*activity)
        sy=cy+r*.02
        for sign in (-1,1):
            sx=cx+sign*r*1.03
            grad=QRadialGradient(QPointF(sx-sr*.25,sy-sr*.3),sr*1.2)
            grad.setColorAt(0,QColor(255,226,166,170)); grad.setColorAt(.55,QColor(86,68,40,210)); grad.setColorAt(1,QColor(8,9,9,250))
            p.setPen(QPen(QColor(244,194,104,150),.8)); p.setBrush(QBrush(grad)); p.drawEllipse(QPointF(sx,sy),sr,sr)
            p.setPen(QPen(QColor(255,226,166,75),.7)); p.drawEllipse(QPointF(sx,sy),sr*.62,sr*.62)

        # Eye: one primitive, many meanings.
        eye_y=cy-r*.20
        mood_open=max(.08,1-fatigue*.62-boredom*.14+max(0,happiness)*.12-fear*.18)
        ew=r*.22; lid=r*.105*mood_open
        pupil=r*(.020+.046*proximity+.012*salience)
        px=cx+(fx-.5)*r*.16; py=eye_y+(fy-.5)*r*.12
        p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,226,166,210+int(35*brightness))))
        eye=QPainterPath(); eye.moveTo(cx-ew,eye_y)
        eye.cubicTo(cx-ew*.4,eye_y-lid,cx+ew*.4,eye_y-lid,cx+ew,eye_y)
        eye.cubicTo(cx+ew*.4,eye_y+lid,cx-ew*.4,eye_y+lid,cx-ew,eye_y); p.drawPath(eye)
        if mode!='out':
            p.setBrush(QBrush(QColor(20,16,10,245))); p.drawEllipse(QPointF(px,py),pupil,pupil)
            p.setPen(QPen(QColor(255,226,166,130),.8)); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(px,py),pupil*1.35,pupil*1.35)
        else:
            p.setPen(QPen(QColor(255,226,166,120),1.0)); p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx+r*.27,cy-r*.29),r*.038,r*.038)
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,226,166,170))); p.drawEllipse(QPointF(cx+r*.27,cy-r*.29),r*.012,r*.012)

        # Mouth remains a single vector stroke.
        mouth_y=cy+r*.27; mw=r*(.21+.045*satisfaction)
        p.setPen(QPen(QColor(255,226,166,220),max(1.4,r*.014)))
        if action=='vocalize':
            amp=r*(.035+.045*pulse); m=QPainterPath()
            for i in range(25):
                u=i/24; x=cx-mw+2*mw*u; y=mouth_y+math.sin(u*math.pi*4+t*8)*amp
                m.moveTo(x,y) if i==0 else m.lineTo(x,y)
            p.drawPath(m)
        else:
            curve=happiness*r*.07
            m=QPainterPath(); m.moveTo(cx-mw,mouth_y)
            m.cubicTo(cx-mw*.45,mouth_y+curve,cx+mw*.45,mouth_y+curve,cx+mw,mouth_y); p.drawPath(m)

        # Final vector rim.
        rim_alpha=105+int(65*brightness)+int(18*pulse)
        p.setPen(QPen(QColor(244,194,104,rim_alpha),1.6)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx,cy),r-.8,r-.8)
        p.end()

    def refresh(self):
        self.face_state=read_json(STATE); self._apply_motor()
        idx=int((self.face_state.get('scheduler') or {}).get('tick_index',0) or 0)
        if idx!=self._render_tick: self._render_tick=idx; self.update()

def main():
    app=QApplication([]); app.setApplicationName('G.A.I.')
    bubble=Bubble(); bubble.show(); bubble.raise_(); bubble._write_proprio('startup')
    timer=QTimer(bubble); timer.timeout.connect(lambda:(bubble.refresh(),bubble.raise_())); timer.start(100)
    return app.exec()

if __name__=='__main__': raise SystemExit(main())
