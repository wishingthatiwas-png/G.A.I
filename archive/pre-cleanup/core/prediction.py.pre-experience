from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,math

PATH=Path("/mnt/gai/memory/predictions.json")
STATE_KEYS=("curiosity","satisfaction","safety","energy","social")

@dataclass
class Prediction:
    action:str
    context:str
    effects:dict[str,float]
    visits:int=0
    error:float=0.0

class PredictiveModel:
    """Tiny action+context world model: predict state change, then learn the error."""
    def __init__(self, learning_rate=0.15):
        self.models:dict[str,Prediction]={}
        self.learning_rate=float(learning_rate)
        self.previous=None
        self.load()

    @staticmethod
    def context_key(context) -> str:
        labels=sorted(str(x) for x in (context or []) if x)
        return "|".join(labels[:16]) or "none"

    def _key(self,action,context):
        return action+"::"+self.context_key(context)

    def load(self):
        if PATH.exists():
            o=json.loads(PATH.read_text())
            self.models={k:Prediction(**v) for k,v in o.get("models",{}).items()}

    def save(self):
        PATH.parent.mkdir(parents=True,exist_ok=True)
        PATH.write_text(json.dumps({"models":{k:asdict(v) for k,v in self.models.items()}},indent=2))

    def predict(self,action,context=None) -> dict[str,float]:
        exact=self.models.get(self._key(action,context))
        if exact:
            return dict(exact.effects)
        # General action model is the fallback when this context is novel.
        matches=[m for m in self.models.values() if m.action==action]
        if not matches:
            return {}
        out={}
        total=sum(m.visits for m in matches) or len(matches)
        for m in matches:
            w=m.visits/total if m.visits else 1/len(matches)
            for k,v in m.effects.items(): out[k]=out.get(k,0.0)+w*v
        return out

    def choose(self,action,context,state):
        predicted=self.predict(action,context)
        self.previous={"action":action,"context":self.context_key(context),
                       "before":{k:float(state.get(k,0.0)) for k in STATE_KEYS},
                       "predicted":predicted}
        return predicted

    def observe(self,state):
        p=self.previous
        if not p: return 0.0
        after={k:float(state.get(k,0.0)) for k in STATE_KEYS}
        model=self.models.setdefault(
            self._key(p["action"],p["context"]),
            Prediction(p["action"],p["context"],{}))
        lr=self.learning_rate
        errors=[]
        for k in STATE_KEYS:
            actual=after[k]-p["before"].get(k,after[k])
            expected=float(p["predicted"].get(k,0.0))
            old=model.effects.get(k,0.0)
            model.effects[k]=old+lr*(actual-old)
            errors.append(abs(actual-expected))
        model.visits+=1
        model.error=sum(errors)/len(errors)
        self.save()
        self.previous=None
        return model.error

    def snapshot(self):
        return {k:asdict(v) for k,v in self.models.items()}
