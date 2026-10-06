from __future__ import annotations
import json, time
from pathlib import Path
ROOT=Path('/mnt/gai'); SCENARIO=ROOT/'laboratory/current_scenario.json'
class SimulatedOrganPack:
    def __init__(self): self.cursor=0; self.scenario=self._load(); self.habituation={}
    def _load(self):
        try: return json.loads(SCENARIO.read_text())
        except Exception: return {'name':'empty','steps':[]}
    def observe(self):
        steps=self.scenario.get('steps') or []
        step=steps[min(self.cursor,len(steps)-1)] if steps else {}
        if steps: self.cursor=(self.cursor+1)%len(steps)
        vision=dict(step.get('vision') or {}) if step.get('vision') is not None else None
        audio=dict(step.get('audio') or {'available':True,'fresh':True,'signal':0.0,'rms':0.0,'auditory':{'transient':0.0,'attended_frequency':0.0}})
        audio.setdefault('available',True); audio.setdefault('fresh',True)
        if vision is not None:
            temporal=vision.setdefault('temporal',{'salience':0.0,'onset':0.0,'velocity':0.0,'acceleration':0.0,'direction':'still'})
            vision.setdefault('patterns',[]); vision.setdefault('concepts',[])
            pattern=(vision.get('patterns') or [{}])[0]; auditory=audio.get('auditory') or {}
            motion_band='high' if float(temporal.get('salience',0))>.25 else 'low'
            sound_band='high' if float(auditory.get('transient',0))>.02 else 'low'
            freq_band=int(round(float(auditory.get('attended_frequency',0))/250.0))
            signature=f"{pattern.get('colour','none')}:{pattern.get('shape','none')}:{motion_band}:{sound_band}:{freq_band}"
            self.habituation={k:max(0.0,v*0.992) for k,v in self.habituation.items()}
            h=min(1.0,float(self.habituation.get(signature,0.0))+0.14)
            self.habituation[signature]=h
            vision['habituation']=round(h,4); vision['sensory_novelty']=round(1.0-h,4)
            temporal['salience']=round(float(temporal.get('salience',0))*(1.0-.75*h),4)
        return {'camera':{'simulated':True,'available':True,'timestamp':time.time()},'audio':audio,'vision':vision}
