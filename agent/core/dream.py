from __future__ import annotations
"""Dream/consolidation engine.

Dream is an internal biological process. It does not control lifecycle or
hardware sleep; it consumes replay and reports what happened.
"""
import time

class DreamEngine:
    def __init__(self, evolution=None):
        self.evolution=evolution
        self.replay=[]
        self.last_report=None

    def queue(self,event):
        if event:
            self.replay.append(dict(event))
            self.replay=self.replay[-500:]

    def run_cycle(self, associative, learner, neural_fabric=None):
        events=list(self.replay[-500:])
        stages=[]
        started=time.time()
        changes=0

        stages.append({"stage":"memory_replay","events":len(events)})
        if events:
            decay_rate=0.003
            try:
                associative.decay(decay_rate)
            except Exception:
                pass
            for event in events:
                stimuli=event.get("stimuli",[])
                if stimuli:
                    try:
                        associative.fire(stimuli,context={"dream_replay":True},
                                         reward=float(event.get("reward",0.0)))
                    except Exception:
                        pass
                    changes += 1

        stages.append({"stage":"association","changes":changes})
        evolution=None
        if self.evolution is not None:
            try:
                evolution=self.evolution.dream_select(events,population=8)
            except Exception:
                evolution=None
        stages.append({"stage":"evolution","result":evolution})

        neural=None
        if neural_fabric is not None:
            try:
                neural=neural_fabric.replay_from_trace()
            except Exception as exc:
                neural={"error":str(exc)}
        stages.append({"stage":"neural_replay","result":neural})

        self.replay.clear()
        self.last_report={
            "timestamp":time.time(),
            "duration_ms":round((time.time()-started)*1000,2),
            "events":len(events),
            "changes":changes,
            "stages":stages,
            "experience_models":learner.snapshot(),
            "complete":True,
        }
        return self.last_report

    def consolidate(self, associative, learner):
        return self.run_cycle(associative,learner,None)
