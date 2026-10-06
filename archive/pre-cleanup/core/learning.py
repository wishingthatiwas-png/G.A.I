from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json

PATH = Path("/mnt/gai/memory/experience_model.json")
STATE_KEYS = ("curiosity", "satisfaction", "safety", "energy", "social")


@dataclass
class ExperienceModel:
    """One compact world model: context -> predicted change -> observed outcome."""
    action: str
    context: str
    effects: dict[str, float]
    visits: int = 0
    error: float = 0.0


class OutcomeLearner:
    """Unified experience/world model kept local and updated online.

    The old action-only outcome learner and action+context predictor are now
    one model.  It remembers what happened, how surprising it was, and uses
    that experience the next time a similar choice appears.
    """
    def __init__(self, learning_rate=0.15):
        self.models: dict[str, ExperienceModel] = {}
        self.learning_rate = float(learning_rate)
        self.previous = None
        self.previous_action = None
        self.last_observed_action = None
        self.last_delta: dict[str, float] = {}
        self.last_prediction: dict[str, float] = {}
        self.last_error = 0.0
        self.last_reward = 0.0
        self.load()

    @staticmethod
    def context_key(context) -> str:
        labels = sorted(str(x) for x in (context or []) if x)
        return "|".join(labels[:16]) or "none"

    def _key(self, action, context) -> str:
        return str(action) + "::" + self.context_key(context)

    def load(self):
        if PATH.exists():
            try:
                obj = json.loads(PATH.read_text())
                self.models = {k: ExperienceModel(**v) for k, v in obj.get("models", {}).items()}
            except Exception:
                self.models = {}

    def save(self):
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps({
            "models": {k: asdict(v) for k, v in self.models.items()}
        }, indent=2))

    def predict(self, action: str, context=None) -> dict[str, float]:
        exact = self.models.get(self._key(action, context))
        if exact:
            return dict(exact.effects)
        matches = [m for m in self.models.values() if m.action == action]
        if not matches:
            return {}
        out = {}
        total = sum(m.visits for m in matches) or len(matches)
        for m in matches:
            weight = m.visits / total if m.visits else 1 / len(matches)
            for key, value in m.effects.items():
                out[key] = out.get(key, 0.0) + weight * value
        return out

    def choose(self, action, context=None, state=None):
        predicted = self.predict(action, context)
        self.previous = {
            "action": action,
            "context": self.context_key(context),
            "before": {k: float((state or {}).get(k, 0.0)) for k in STATE_KEYS},
            "predicted": predicted,
        }
        self.previous_action = action
        self.last_prediction = predicted
        return predicted

    def observe(self, state):
        previous = self.previous
        if not previous:
            return 0.0
        after = {k: float(state.get(k, 0.0)) for k in STATE_KEYS}
        model = self.models.setdefault(
            self._key(previous["action"], previous["context"]),
            ExperienceModel(previous["action"], previous["context"], {})
        )
        lr = self.learning_rate
        self.last_delta = {}
        errors = []
        for key in STATE_KEYS:
            actual = after[key] - previous["before"].get(key, after[key])
            expected = float(previous["predicted"].get(key, 0.0))
            self.last_delta[key] = actual
            old = model.effects.get(key, 0.0)
            model.effects[key] = old + lr * (actual - old)
            errors.append(abs(actual - expected))
        model.visits += 1
        model.error = sum(errors) / len(errors)
        self.last_error = model.error
        self.last_observed_action = previous["action"]
        self.previous = None
        self.save()
        return model.error

    @property
    def models_snapshot(self):
        return {k: asdict(v) for k, v in self.models.items()}

    def snapshot(self):
        return self.models_snapshot
