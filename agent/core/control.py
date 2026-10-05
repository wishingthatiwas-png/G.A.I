from __future__ import annotations
from dataclasses import dataclass
from .signals import SignalBus
from .reward import MotivationSystem
from .learning import OutcomeLearner
from .prediction import PredictiveModel

@dataclass
class ControlDecision:
    action:str
    score:float
    reason:str
    expected_reward:float=0.0

class ControlCentre:
    """Chooses actions by predicted outcomes against current drives."""
    def __init__(self,bus:SignalBus,learner=None,predictor=None):
        self.bus=bus
        self.motivation=MotivationSystem()
        self.learner=learner or OutcomeLearner()
        self.predictor=predictor or PredictiveModel()
        self.params={}

    def candidates(self): return ["rest","maintain","interact","explore"]

    def decide(self,state=None,context=None) -> ControlDecision:
        fatigue=self.bus.get("fatigue"); threat=self.bus.get("threat")
        novelty=self.bus.get("novelty"); curiosity=self.bus.get("curiosity")
        interaction=self.bus.get("interaction"); maintain=self.bus.get("maintenance")
        novelty_weight=float(self.params.get("novelty_weight",1.0))
        reward_gain=float(self.params.get("reward_gain",1.0))
        base={"rest":.9*fatigue+.8*threat,"maintain":.9*maintain,
              "interact":.8*interaction+.2*novelty_weight*novelty,
              "explore":.7*curiosity+.6*novelty_weight*novelty-.5*threat}
        current=self.motivation_values(state)
        scores={}
        predictions={}
        for action in self.candidates():
            effects=self.predictor.predict(action,context)
            if not effects: effects=self.learner.predict(action)
            predictions[action]=effects
            future=dict(current)
            for key,effect in effects.items(): future[key]=future.get(key,0.0)+float(effect)
            expected=self.motivation.score_outcome(current,future)
            scores[action]=base[action]+reward_gain*expected
        action,score=max(scores.items(),key=lambda x:x[1])
        return ControlDecision(action,score,f"predicted:{predictions[action]}",scores[action]-base[action])

    @staticmethod
    def motivation_values(state):
        if state is None:
            return {"curiosity":0.5,"satisfaction":0.5,"safety":0.0,"energy":0.0,"social":0.0}
        return {"curiosity":state.curiosity,"satisfaction":state.satisfaction,
                "safety":state.stress,"energy":state.fatigue,"social":0.0}
