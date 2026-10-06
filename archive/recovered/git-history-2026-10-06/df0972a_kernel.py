import json
import logging
import time
from pathlib import Path
from .state import InternalState
from .drives import DriveState
from .world import WorldState
from .memory import Memory
from .signals import SignalBus
from .control import ControlCentre
from .learning import OutcomeLearner
from .prediction import PredictiveModel
from .lifecycle import Lifecycle
from .dream import DreamEngine
from .evolution import EvolutionEngine
from .power import level_and_charging
from .working_memory import WorkingMemoryCell
from memory.engram import AssociativeMemory
from memory.semantic import SemanticNetwork
from actions.safe import SafeActions
from perception.screen import snapshot as screen_snapshot
from perception.senses import Senses
from perception.system import snapshot as system_snapshot
from perception.hardware import snapshot as hardware_snapshot

ROOT=Path('/mnt/gai'); CONFIG=ROOT/'config/agent.json'

class Kernel:
    def __init__(self):
        cfg=json.loads(CONFIG.read_text()); self.cfg=cfg
        self.state=InternalState(); self.drives=DriveState(); self.world=WorldState()
        self.last_system={}; self.last_hardware={}; self.last_action={'type':'none'}
        self.actions=SafeActions(); self.last_screen={}; self.senses=Senses(); self.last_senses={}
        self.memory=Memory(cfg['memory_db']); self.associative=AssociativeMemory(); self.semantic=SemanticNetwork()
        self.bus=SignalBus(); self.learner=OutcomeLearner(); self.predictor=PredictiveModel()
        self.nervous=self.bus.nervous
        self.nervous.register_component("kernel",kind="core",version="0.1.0",sleep_capable=False)
        self.nervous.register_component("perception",kind="planned")
        self.nervous.register_component("memory",kind="planned")
        self.nervous.register_component("prediction",kind="planned")
        self.nervous.register_component("control",kind="planned")
        self.nervous.register_component("language",kind="planned")
        self.control=ControlCentre(self.bus,self.learner,self.predictor)
        self.lifecycle=Lifecycle(); self.evolution=EvolutionEngine(); self.dream=DreamEngine(self.evolution)
        self.dream_last_report=None
        self.working_memory=WorkingMemoryCell(self.nervous).start()
        self.sync_phenotype()
        Path(cfg['log_file']).parent.mkdir(parents=True,exist_ok=True)
        logging.basicConfig(filename=cfg['log_file'],level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
        self.log=logging.getLogger('gai')

    def sync_phenotype(self):
        genes=self.evolution.phenotype()
        self.learner.learning_rate=genes["prediction_lr"]
        self.predictor.learning_rate=genes["prediction_lr"]
        self.associative.association_gain=genes["association_gain"]
        self.control.params=genes

    def drive_values(self):
        return {'curiosity':self.state.curiosity,'satisfaction':self.state.satisfaction,
                'safety':self.state.stress,'energy':self.state.fatigue,'social':0.0}

    def snapshot(self):
        return {'state':self.state.snapshot(),'drives':vars(self.drives),'world':vars(self.world),
                'signals':self.bus.snapshot(),'learning':self.bus.learning_snapshot(),
                'nervous':self.bus.nervous_snapshot(),
                'working_memory':self.working_memory.snapshot(),
                'outcome_model':{k:vars(v) for k,v in self.learner.models.items()},
                'predictions':self.predictor.snapshot(),
                'control':vars(self.control.decide(self.state, self.current_context() if self.last_senses else None)),
                'perception':{'system':self.last_system,'hardware':self.last_hardware,'screen':self.last_screen,'senses':self.last_senses},
                'action':self.last_action,'dream_report':self.dream_last_report}

    def current_context(self):
        vision=self.last_senses.get('vision') or {}
        concepts=vision.get('concepts',[])
        context=['camera' if self.last_senses.get('camera') else 'no_camera']
        context.extend(concepts[:16])
        audio=self.last_senses.get('audio') or {}
        if isinstance(audio,dict) and float(audio.get('rms',0.0))>.03: context.append('sound')
        context.append(self.state.mode)
        return context

    def emit(self,kind,payload=None,**kwargs):
        return self.nervous.publish(kind,payload,source="kernel",**kwargs)

    def tick(self):
        self.nervous.heartbeat("kernel",detail={"phase":self.lifecycle.state.phase.value})
        tick_event=self.emit("tick.started",{"uptime":self.state.uptime},priority="background")
        correlation=tick_event.event_id
        self.sync_phenotype()
        self.state.update_time()
        self.emit("perception.request",{"domains":["system","hardware","screen","camera","audio"]},
                  priority="normal",correlation_id=correlation)
        self.last_system=system_snapshot(); self.last_hardware=hardware_snapshot(); self.last_screen=screen_snapshot()
        self.last_senses=self.senses.observe()
        perception={'system':self.last_system,'hardware':self.last_hardware,'screen':self.last_screen,'senses':self.last_senses}
        self.world.observe(perception); self.drives.update(self.state,perception)
        self.emit("drive.update",self.drive_values(),priority="control",
                  correlation_id=correlation,provenance="internal")

        actual=self.drive_values()
        prediction_error=self.predictor.observe(actual)
        outcome_error=self.learner.observe(actual)
        self.emit("prediction.error",{"value":prediction_error,"outcome_error":outcome_error},
                  priority="control",correlation_id=correlation,provenance="learned")

        load=float(self.last_system.get('load_1m',0.0)); memory=float(self.last_system.get('memory_percent',0.0))/100.0
        vision=self.last_senses.get('vision') or {}; concepts=vision.get('concepts',[])
        audio=self.last_senses.get('audio') or {}
        sound=min(1.0,float(audio.get('rms',0.0))/0.08) if isinstance(audio,dict) else 0.0
        novelty=1.0 if any(c not in self.associative.neurons for c in concepts) else 0.0
        self.emit("perception.observation",{"camera":bool(self.last_senses.get("camera")),
                  "concepts":concepts,"sound_level":sound},priority="normal",
                  correlation_id=correlation,confidence=1.0,provenance="sensor",
                  novelty=novelty)
        self.bus.publish('fatigue',self.state.fatigue,adaptive=True)
        self.bus.publish('threat',min(1.0,load/2.0+memory*.25),adaptive=True)
        self.bus.publish('novelty',novelty,adaptive=True)
        self.bus.publish('curiosity',self.state.curiosity,adaptive=True)
        self.bus.publish('interaction',.65 if sound>.03 else 0.0,adaptive=True)
        self.bus.publish('maintenance',min(1.0,load/2.0+memory*.5),adaptive=True)

        context=self.current_context()
        decision=self.control.decide(self.state,context)
        self.emit("control.decision",{"action":decision.action,"score":decision.score,
                  "expected_reward":decision.expected_reward,"context":context},priority="control",
                  correlation_id=correlation,provenance="predicted")
        self.state.mode=decision.action
        self.predictor.choose(decision.action,context,self.drive_values())
        self.learner.choose(decision.action)
        self.emit("action.request",{"action":decision.action,"reason":decision.reason,
                  "expected_reward":decision.expected_reward},priority="control",
                  correlation_id=correlation,provenance="controller")
        self.last_action={'type':decision.action,'reason':decision.reason,'score':decision.score,
                          'expected_reward':decision.expected_reward,'prediction_error':prediction_error,
                          'outcome_error':outcome_error}
        self.actions.save_observation(perception)

        stimuli=['system','camera_present' if self.last_senses.get('camera') else 'camera_absent',self.state.mode]
        stimuli.extend(concepts[:24])
        if sound>.03: stimuli.append('sound_present')
        emotions={'curiosity':self.state.curiosity,'stress':self.state.stress,'satisfaction':self.state.satisfaction,'fatigue':self.state.fatigue}
        reward=self.state.satisfaction-self.state.stress
        self.emit("reward.signal",{"value":reward,"drives":self.drive_values()},priority="control",
                  correlation_id=correlation,provenance="internal")
        self.associative.fire(stimuli,emotions=emotions,context={'action':self.last_action,'observation':self.world.observation_count},reward=reward)
        self.dream.queue({'stimuli':stimuli,'emotions':emotions,'reward':reward,
                          'prediction_error':prediction_error,'action':self.last_action,
                          'context':context})
        self.memory.remember('tick',{'mode':self.state.mode,'drives':vars(self.drives),'action':self.last_action,
                                     'signals':self.bus.snapshot(),'stimuli':stimuli,'context':context})
        self.emit("memory.enqueued",{"stimuli":stimuli,"reward":reward},priority="background",
                  correlation_id=correlation,provenance="experience")
        self.emit("tick.completed",{"action":self.state.mode,"prediction_error":prediction_error},
                  priority="background",correlation_id=correlation)
        self.nervous.dispatch(128)
        snap=self.snapshot(); snap['lifecycle']=vars(self.lifecycle.state)
        (ROOT/'state/runtime.json').write_text(json.dumps(snap,indent=2)); return snap

    def lifecycle_step(self):
        level,plugged=level_and_charging()
        state=self.lifecycle.update_power(level,plugged)
        phase=state.phase.value
        self.nervous.set_phase(phase)
        self.emit("lifecycle.transition",{"phase":phase,"battery":level,"charging":plugged},
                  priority="control",provenance="power")

        if phase=="pre_sleep":
            self.lifecycle.enter_dream()
            self.nervous.set_phase(self.lifecycle.state.phase.value)
            self.dream_last_report=self.dream.consolidate(self.associative,self.learner)
            self.log.info("dream cycle %s complete",state.dream_cycles)

        elif phase=="wake":
            self.lifecycle.finish_wake()
            self.nervous.set_phase(self.lifecycle.state.phase.value)
            self.log.info("wake transition: %s",state.reason)

        return self.lifecycle.state

    def run(self):
        self.log.info('G.A.I. kernel starting')
        while True:
            phase=self.lifecycle_step().phase.value
            if phase=="awake":
                self.tick()
                time.sleep(self.cfg.get('tick_seconds',2))
            elif phase=="dream":
                time.sleep(1.0)

if __name__=='__main__': Kernel().run()
