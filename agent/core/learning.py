from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
import random

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
        # Persistence is intentionally decoupled from the fast biological clock.
        # The in-memory model learns every tick; disk checkpoints every 5 visits.
        if sum(m.visits for m in self.models.values()) % 5 == 0:
            self.save()
        return model.error

    @property
    def models_snapshot(self):
        return {k: asdict(v) for k, v in self.models.items()}

    def snapshot(self):
        return self.models_snapshot


@dataclass
class ExperiencePreference:
    value: float = 0.0
    visits: int = 0
    last_reward: float = 0.0


class ExperiencePolicy:
    """Model-free plastic action preference learned only from consequences."""
    PATH = Path("/mnt/gai/memory/experience_policy.json")

    def __init__(self, learning_rate=0.18, decay=0.002):
        self.learning_rate = float(learning_rate)
        self.decay = float(decay)
        self.preferences = {}
        self.by_action = {}
        self.load()

    @staticmethod
    def context_key(context):
        labels = sorted({str(x) for x in (context or []) if x})
        return "|".join(labels[:12]) or "none"

    def _key(self, action, context):
        return f"{action}::{self.context_key(context)}"

    def load(self):
        if not self.PATH.exists():
            return
        try:
            raw = json.loads(self.PATH.read_text())
            self.preferences = {k: ExperiencePreference(**v) for k, v in raw.get("preferences", {}).items()}
            self.by_action = {}
            for k, pref in self.preferences.items():
                action = k.split("::", 1)[0]
                self.by_action.setdefault(action, []).append(pref)
        except Exception:
            self.preferences = {}
            self.by_action = {}

    def save(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        self.PATH.write_text(json.dumps({"preferences": {k: asdict(v) for k, v in self.preferences.items()}}, indent=2))

    def values(self, actions, context):
        out = {a: self.preferences.get(self._key(a, context), ExperiencePreference()).value for a in actions}
        for action in actions:
            if out[action] != 0.0:
                continue
            matches = [p for p in self.by_action.get(action, []) if p.visits]
            if matches:
                out[action] = sum(p.value * p.visits for p in matches) / sum(p.visits for p in matches)
        return out

    def sample(self, actions, base_scores, context, temperature=0.55):
        learned = self.values(actions, context)
        combined = {a: float(base_scores[a]) + 1.35 * learned.get(a, 0.0) for a in actions}
        peak = max(combined.values()) if combined else 0.0
        weights = {a: math.exp(max(-30.0, min(30.0, (v - peak) / max(0.15, temperature)))) for a, v in combined.items()}
        total = sum(weights.values()) or 1.0
        pick = random.random() * total
        chosen = actions[-1]
        running = 0.0
        for action in actions:
            running += weights[action]
            if pick <= running:
                chosen = action
                break
        return chosen, combined, learned

    def observe(self, action, context, reward):
        reward = max(-1.0, min(1.0, float(reward)))
        key = self._key(action, context)
        if key in self.preferences:
            pref = self.preferences[key]
        else:
            pref = ExperiencePreference()
            self.preferences[key] = pref
            self.by_action.setdefault(action, []).append(pref)
        pref.value += self.learning_rate * (reward - pref.value)
        pref.value *= (1.0 - self.decay)
        pref.value = max(-1.0, min(1.0, pref.value))
        pref.visits += 1
        pref.last_reward = reward
        # Keep action plasticity immediate; checkpoint the preference bank every
        # 5 visits instead of serializing the entire bank on every tick.
        if sum(p.visits for p in self.preferences.values()) % 5 == 0:
            self.save()
        return pref.value

    def snapshot(self):
        return {k: asdict(v) for k, v in self.preferences.items()}
