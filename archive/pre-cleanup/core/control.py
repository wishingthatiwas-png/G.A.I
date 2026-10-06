from __future__ import annotations
from dataclasses import dataclass
from .signals import SignalBus


@dataclass
class ControlDecision:
    action: str
    score: float
    reason: str
    expected_reward: float = 0.0


class ControlCentre:
    """Chooses from predicted outcomes against the current body/feel state."""
    def __init__(self, bus: SignalBus, learner=None, predictor=None):
        self.bus = bus
        self.learner = learner or predictor
        self.predictor = self.learner
        self.params = {}

    def candidates(self):
        return ["rest", "maintain", "interact", "explore"]

    def decide(self, state=None, context=None) -> ControlDecision:
        fatigue = self.bus.get("fatigue")
        threat = self.bus.get("threat")
        novelty = self.bus.get("novelty")
        curiosity = self.bus.get("curiosity")
        interaction = self.bus.get("interaction")
        maintain = self.bus.get("maintenance")
        boredom = float(getattr(state, "boredom", 0.0) if state is not None else 0.0)
        novelty_weight = float(self.params.get("novelty_weight", 1.0))
        reward_gain = float(self.params.get("reward_gain", 1.0))

        base = {
            "rest": .9 * fatigue + .8 * threat,
            "maintain": .9 * maintain,
            "interact": .8 * interaction + .2 * novelty_weight * novelty,
            "explore": .7 * curiosity + .6 * novelty_weight * novelty - .5 * threat,
        }

        current = self.motivation_values(state)
        scores = {}
        predictions = {}
        for action in self.candidates():
            effects = self.learner.predict(action, context)
            predictions[action] = effects
            future = dict(current)
            for key, effect in effects.items():
                future[key] = future.get(key, 0.0) + float(effect)

            expected = self._outcome_value(current, future)
            # Boredom changes how much novelty matters in the predicted future;
            # it is not an action command and cannot force exploration.
            predicted_novelty = max(0.0, float(effects.get("curiosity", 0.0)))
            expected += boredom * novelty_weight * .35 * predicted_novelty
            scores[action] = base[action] + reward_gain * expected

        action, score = max(scores.items(), key=lambda x: x[1])
        return ControlDecision(
            action, score, f"predicted:{predictions[action]}",
            scores[action] - base[action]
        )

    @staticmethod
    def _outcome_value(before, after):
        # A small local value function; the experience model supplies the
        # future change rather than a pile of emotion->action rules.
        weights = {"curiosity": .45, "satisfaction": .55, "safety": -1.0,
                   "energy": -.55, "social": .25}
        return sum(weights[k] * (after.get(k, 0.0) - before.get(k, 0.0)) for k in weights)

    @staticmethod
    def motivation_values(state):
        if state is None:
            return {"curiosity": .5, "satisfaction": .5, "safety": 0.0,
                    "energy": 0.0, "social": 0.0}
        return {
            "curiosity": state.curiosity,
            "satisfaction": state.satisfaction,
            "safety": state.stress,
            "energy": state.fatigue,
            "social": 0.0,
        }
