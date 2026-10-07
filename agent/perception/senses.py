from __future__ import annotations
from pathlib import Path
import json, time
import cv2
from .vision import analyse, spatial_summary, TemporalVision, concepts
from .vision.concepts import pattern_signature
from .sight_focus import read as read_focus, set_focus
from .retina import ReactiveRetina

class Senses:
    """Persistent visual/audio organs with one selected visual stream."""
    HABITUATION_PATH = Path('/mnt/gai/state/sensory_habituation.json')
    SCREEN_FRAME = Path('/mnt/gai/state/screen_stream.jpg')

    def __init__(self):
        self.organ_mode='real'
        try:
            self.organ_mode=str(json.loads(Path('/mnt/gai/state/organ_mode.json').read_text()).get('mode','real'))
        except Exception: pass
        self.simulated=None
        if self.organ_mode=='simulated':
            from laboratory.virtual_organs import SimulatedOrganPack
            self.simulated=SimulatedOrganPack()
        self.camera=None
        self.temporal={'in':TemporalVision()}
        self.retina={'in':ReactiveRetina(),'out':ReactiveRetina()}
        self.habituation=self._load_habituation()
        self.last_signature=None

    def _load_habituation(self):
        try:
            obj=json.loads(self.HABITUATION_PATH.read_text())
            return {str(k):max(0.0,min(1.0,float(v))) for k,v in obj.items() if len(str(k).split(':'))==5}
        except Exception: return {}

    def _save_habituation(self):
        self.HABITUATION_PATH.parent.mkdir(parents=True,exist_ok=True)
        self.habituation=dict(sorted(self.habituation.items(),key=lambda item:item[1],reverse=True)[:64])
        self.HABITUATION_PATH.write_text(json.dumps(self.habituation,separators=(',',':')))

    def _audio_from_organ(self):
        path=Path('/mnt/gai/state/audio_input.json')
        try:
            payload=json.loads(path.read_text())
            age=max(0.0,time.time()-float(payload.get('timestamp',0.0)))
            payload['fresh']=age<=2.5; payload['age_seconds']=round(age,3); return payload
        except Exception as exc:
            return {'available':False,'fresh':False,'error':type(exc).__name__}

    @staticmethod
    def _signature(vision,audio):
        temporal=(vision or {}).get('temporal') or {}
        patterns=(vision or {}).get('patterns') or []
        pattern=patterns[0] if patterns else {}
        auditory=(audio or {}).get('auditory') or {}
        freq=float(auditory.get('attended_frequency',0.0) or 0.0)
        freq_band=int(round(freq/250.0)) if freq else 0
        colour=str(pattern.get('colour','none')); shape=str(pattern.get('shape','none'))
        motion_band='high' if float(temporal.get('salience',0.0) or 0.0)>.25 else 'low'
        sound_band='high' if float(auditory.get('transient',0.0) or 0.0)>.02 else 'low'
        return f'{colour}:{shape}:{motion_band}:{sound_band}:{freq_band}'

    def _apply_habituation(self,signature):
        self.habituation={key:max(0.0,value*.992) for key,value in self.habituation.items()}
        updated=min(1.0,float(self.habituation.get(signature,0.0))+.14)
        self.habituation[signature]=updated
        # Persist habituation periodically rather than synchronously on every
        # sensory observation; the in-memory value remains authoritative live.
        self._habituation_dirty = True
        if not hasattr(self, '_habituation_save_counter'):
            self._habituation_save_counter = 0
        self._habituation_save_counter += 1
        if self._habituation_save_counter >= 25:
            self._save_habituation()
            self._habituation_save_counter = 0
            self._habituation_dirty = False
        return updated

    def _selected_visual_frame(self, mode):
        # V1 inward-virtual visual boundary: the organism sees its persistent
        # desktop/habitat field only. Physical webcam access is disabled.
        mode = 'in'
        try:
            frame = cv2.imread(str(self.SCREEN_FRAME))
            if frame is not None:
                age = time.time() - self.SCREEN_FRAME.stat().st_mtime
                if age <= 2.0:
                    return {
                        'frame': frame,
                        'path': str(self.SCREEN_FRAME),
                        'available': True,
                        'streaming': True,
                        'mode': 'in',
                        'age_seconds': round(max(0.0, age), 3),
                        'width': int(frame.shape[1]),
                        'height': int(frame.shape[0]),
                    }
        except Exception:
            pass
        return {'available': False, 'mode': 'in', 'streaming': True, 'reason': 'screen_unavailable'}

    def observe(self):
        if self.organ_mode=='simulated' and self.simulated is not None:
            return self.simulated.observe()

        focus=read_focus()
        if focus.get('mode')!='in':
            focus=set_focus(mode='in', target='virtual_habitat', reason='inward_virtual_environment')
        mode='in'
        visual=self._selected_visual_frame(mode)
        audio=self._audio_from_organ()
        vision=None
        if visual.get('available'):
            frame=visual.pop('frame')
            # Camera owns the persistent JPEG mirror; do not re-encode the same
            # frame synchronously inside the CNS perception path.
            retina=self.retina[mode].inspect(frame)
            if retina.get('reflex')=='orient':
                focus=set_focus(mode='in', x=retina.get('x', focus.get('x', 0.5)),
                                y=retina.get('y', focus.get('y', 0.5)),
                                radius=min(0.30, max(0.14, float(focus.get('radius', 0.18)) * 1.35)),
                                target='retina_reflex', reason='automatic_large_movement')
            # The retina is the cheap gate for the expensive foveal/object pass.
            # Stable frames reuse the last detailed scene while temporal sensing
            # continues every observation.
            temporal=self.temporal[mode].compare(frame)
            previous_vision=getattr(self, '_last_vision', {}).get(mode)
            stable_scene=(previous_vision is not None and retina.get('reflex') == 'none'
                          and not temporal.get('changed', False))
            if stable_scene:
                vision=dict(previous_vision)
            else:
                vision=analyse(frame)
                vision['objects']=spatial_summary(vision['objects'])
                self._last_vision=getattr(self, '_last_vision', {})
                self._last_vision[mode]=dict(vision)
            vision['retina']=retina
            # Continuous orienting: reflexes catch large changes; temporal salience
            # also steers attention toward ordinary moving objects without waiting
            # for the CC. This is the fast bottom-up eye loop.
            centroid=temporal.get('centroid')
            if centroid and float(temporal.get('salience',0.0)) >= 0.28 and vision.get('retina',{}).get('reflex') != 'orient':
                focus=set_focus(
                    mode='in',
                    x=centroid.get('x', focus.get('x',0.5)),
                    y=centroid.get('y', focus.get('y',0.5)),
                    radius=min(0.26,max(0.12,float(focus.get('radius',0.18))*1.12)),
                    target='temporal_orient',
                    reason='automatic_motion_attention',
                )
            if vision.get('retina', {}).get('reflex')=='orient':
                temporal['salience']=max(float(temporal.get('salience', 0.0)), float(vision['retina'].get('strength', 0.0)))
            vision['temporal']=temporal
            vision['patterns']=pattern_signature(vision)
            vision['concepts']=concepts(vision,temporal)
            signature=self._signature(vision,audio)
            habituation=self._apply_habituation(signature)
            vision['habituation']=round(habituation,4)
            vision['sensory_novelty']=round(1.0-habituation,4)
            vision['stimulus_signature']=signature
            vision['source_mode']=mode
            temporal['salience']=round(float(temporal.get('salience',0.0))*(1.0-.75*habituation),4)
            visual['brightness_interest']=round(min(1.0, float(temporal.get('brightness_change',0.0) or 0.0) * 8.0),4)
            visual['change_interest']=round(max(float(temporal.get('salience',0.0)), visual['brightness_interest']),4)
            novelty_gate = float(vision.get('sensory_novelty', 0.0) or 0.0) >= 0.65
            visual['memory_worthy']=bool(visual['change_interest'] >= 0.12 or novelty_gate)
            visual['environment_key']=signature
            visual['processed']=True
        else:
            visual['processed']=False
        cam={'available':False,'streaming':False,'mode':'out','selected':False,'disabled':True,'reason':'webcam_disabled'}
        return {'camera':cam,'visual_stream':{k:v for k,v in visual.items() if k!='frame'},'audio':audio,'vision':vision,'focus':focus}

    def close(self): pass
