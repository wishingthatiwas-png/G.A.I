from __future__ import annotations
import json, math, time
from pathlib import Path

from .neural_population import NeuralPopulation
from .compute_fabric import ComputeFabric
from .scaling import neural_population_target

ROOT=Path('/mnt/gai'); PATH=ROOT/'state/neural_fabric.json'

class NeuralFabric:
    """Sparse adaptive routing layer; plasticity expands during sleep, not CC commands."""
    def __init__(self, config=None):
        self.edges={}
        self.phase='awake'
        self.generation=0
        self.plasticity={'awake':0.015,'pre_sleep':0.045,'dream':0.12,'wake':0.035}
        self.stats={'awake_updates':0,'dream_updates':0,'pruned':0,'maintenance':0,'physical_sleep_sessions':0}
        self.sleep_session=None
        self.population=NeuralPopulation(target=neural_population_target(config or {}), maximum=1024)
        self.compute=ComputeFabric()
        self.load()

    def load(self):
        try:
            obj=json.loads(PATH.read_text())
            self.edges=obj.get('edges',{}); self.generation=int(obj.get('generation',0))
            self.stats.update(obj.get('stats',{}))
        except Exception: pass

    def save(self):
        PATH.parent.mkdir(parents=True,exist_ok=True)
        PATH.write_text(json.dumps({'generation':self.generation,'phase':self.phase,'edges':self.edges,'stats':self.stats},separators=(',',':')))

    @staticmethod
    def _key(attention,action):
        mod=str((attention or {}).get('modality','none')); target=str((attention or {}).get('target','nothing'))
        return f'{mod}:{target}->{action}'

    def set_phase(self,phase):
        self.phase=str(phase or 'awake')

    def ingest(self, signal):
        signal = dict(signal or {})
        self.stats['signals'] = int(self.stats.get('signals', 0)) + 1
        return dict(signal)

    def select_attention(self, senses, fallback=None):
        senses = senses or {}
        candidates = []
        vision = senses.get('vision') or {}
        temporal = vision.get('temporal') or {}
        v_sal = float(temporal.get('salience', 0.0) or 0.0)
        v_nov = float(vision.get('sensory_novelty', 0.0) or 0.0)
        if max(v_sal, v_nov) > 0.02:
            candidates.append({'modality':'vision','target':'moving_region' if v_sal >= v_nov else 'visual_event','salience':max(v_sal,v_nov),'reason':'neural_visual_gate'})
        audio = senses.get('audio') or {}
        auditory = audio.get('auditory') or {}
        rms = float(auditory.get('rms', 0.0) or 0.0)
        if rms > 0.002:
            candidates.append({'modality':'audio','target':'sound_event','salience':min(1.0,rms*8.0),'reason':'neural_auditory_gate'})
        if not candidates and fallback:
            try:
                result = dict(fallback())
                result['authority'] = 'neural_fabric_fallback'
                return result
            except Exception:
                pass
        if not candidates:
            candidates = [{'modality':'internal','target':'homeostasis','salience':0.05,'reason':'neural_default'}]
        for c in candidates:
            prefix = str(c['modality']) + ':' + str(c['target']) + '->'
            learned = [float(v.get('weight',0.0)) for k,v in self.edges.items() if k.startswith(prefix)]
            c['learned_weight'] = max(learned or [0.0])
            c['score'] = min(1.0, 0.8*float(c['salience']) + 0.2*c['learned_weight'])
        selected = max(candidates, key=lambda x: float(x.get('score',0.0)))
        self.stats['selections'] = int(self.stats.get('selections',0)) + 1
        return {'selected':selected,'candidates':candidates,'authority':'neural_fabric'}

    def route(self, attention, action, reward=0.0, prediction_error=0.0):
        self.record_choice(attention, action, reward, prediction_error)
        return self._key(attention, action)

    def record_choice(self,attention,action,reward=0.0,prediction_error=0.0):
        key=self._key(attention,action)
        edge=self.edges.setdefault(key,{'weight':0.08,'visits':0,'reward':0.0,'error':0.0,'last':0.0})
        edge['visits']+=1; edge['reward']=0.92*float(edge.get('reward',0.0))+0.08*float(reward)
        edge['error']=0.92*float(edge.get('error',0.0))+0.08*abs(float(prediction_error))
        lr=self.plasticity.get(self.phase,0.015)
        target=max(0.0,min(1.0,.5+.5*float(reward)))
        edge['weight']=max(0.0,min(1.0,float(edge.get('weight',.08)) + lr*(target-float(edge.get('weight',.08)))))
        edge['last']=time.time()
        self.stats['awake_updates']+=1 if self.phase=='awake' else 0
        if self.phase=='dream': self.stats['dream_updates']+=1
        self.population.recruit({'modality': key.split(':',1)[0], 'salience': max(0.0, min(1.0, float(edge.get('weight', 0.0))))}, amount=6)
        self.compute.route(workload=0.05, urgency=max(0.2, float(edge.get('weight', 0.0))), modality=key.split(':',1)[0], locality='gpu')

    def replay_from_trace(self):
        events=[]
        trace=ROOT/'state/v1_trace.jsonl'
        try:
            events=[json.loads(x) for x in trace.read_text().splitlines()[-500:]]
        except Exception: pass
        return self.replay(events)

    def replay(self,events):
        self.phase='dream'
        for event in list(events or [])[-500:]:
            action=event.get('action') or (event.get('action_result') or {}).get('action')
            if isinstance(action,dict): action=action.get('type') or action.get('action')
            attention=event.get('attention') or {}
            if not isinstance(attention,dict): continue
            if not attention.get('modality'):
                continue
            if not action: continue
            self.record_choice(attention,action,float(event.get('reward',event.get('outcome_reward',0.0))),float(event.get('prediction_error',0.0)))
        self.generation+=1
        self.maintenance(dream=True)
        self.save()
        return {'generation':self.generation,'edges':len(self.edges),'plasticity':self.plasticity['dream']}

    def maintenance(self,dream=False):
        factor=0.996 if dream else 0.998
        for e in self.edges.values():
            e['weight']=max(0.0,min(1.0,float(e.get('weight',0))*factor + float(e.get('reward',0))*0.01))
            e['reward']*=factor; e['error']*=factor
        before=len(self.edges)
        if len(self.edges)>256:
            keep=sorted(self.edges.items(),key=lambda kv:(float(kv[1].get('weight',0)),int(kv[1].get('visits',0))),reverse=True)[:256]
            self.edges=dict(keep)
        self.edges={k:v for k,v in self.edges.items() if float(v.get('weight',0))>.015 or int(v.get('visits',0))>=2}
        self.stats['pruned']+=max(0,before-len(self.edges)); self.stats['maintenance']+=1

    def begin_physical_sleep(self, reason='lid_closed'):
        self.sleep_session={'started':time.time(),'reason':reason,'generation':self.generation}
        self.stats['physical_sleep_sessions']=int(self.stats.get('physical_sleep_sessions',0))+1
        self.save()
        return dict(self.sleep_session)

    def end_physical_sleep(self, reason='lid_opened'):
        session=dict(self.sleep_session or {})
        session['ended']=time.time(); session['duration']=max(0.0,session['ended']-float(session.get('started',session['ended'])))
        session['wake_reason']=reason
        self.sleep_session=None
        self.phase='wake'
        self.save()
        return session

    def snapshot(self):
        top=sorted(self.edges.items(),key=lambda kv:float(kv[1].get('weight',0)),reverse=True)[:12]
        return {'phase':self.phase,'generation':self.generation,'edge_count':len(self.edges),
                'population':self.population.snapshot(),'compute_fabric':self.compute.snapshot(),
                'plasticity':self.plasticity.get(self.phase,.015),'top_routes':[
                    {'route':k,**{x:round(float(v.get(x,0)),4) for x in ('weight','reward','error')},'visits':int(v.get('visits',0))}
                    for k,v in top],'stats':dict(self.stats)}
