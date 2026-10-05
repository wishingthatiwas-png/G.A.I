from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, math, time

PATH = Path("/mnt/gai/memory/outcome_model.json")

@dataclass
class OutcomeModel:
    action: str
    effects: dict[str, float]
    visits: int = 0
    error: float = 0.0

class OutcomeLearner:
    """Learns action -> outcome effects from observed changes.

    This deliberately uses tiny online updates rather than an LLM.
    """
    def __init__(self, learning_rate=0.15):
        self.models: dict[str, OutcomeModel] = {}
        self.learning_rate=float(learning_rate)
        self.previous: dict[str,float] | None = None
        self.previous_action: str | None = None
        self.load()

    def load(self):
        if PATH.exists():
            obj=json.loads(PATH.read_text())
            self.models={k:OutcomeModel(**v) for k,v in obj.get("models",{}).items()}

    def save(self):
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps({"models":{k:asdict(v) for k,v in self.models.items()}},indent=2))

    def predict(self, action: str) -> dict[str,float]:
        return dict(self.models.get(action, OutcomeModel(action, {})).effects)

    def choose(self, action: str):
        self.previous_action = action

    def observe(self, state: dict[str,float]):
        if self.previous_action is None or self.previous is None:
            self.previous = dict(state)
            return 0.0
        model=self.models.setdefault(self.previous_action, OutcomeModel(self.previous_action, {}))
        total_error=0.0
        lr=self.learning_rate
        for key, after in state.items():
            before=self.previous.get(key, after)
            delta=float(after)-float(before)
            old=model.effects.get(key,0.0)
            model.effects[key]=old + lr*(delta-old)
            total_error += abs(delta-old)
        model.visits += 1
        model.error = total_error / max(1,len(state))
        self.previous=dict(state)
        self.save()
        return total_error
