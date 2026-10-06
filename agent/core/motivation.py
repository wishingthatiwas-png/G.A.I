from __future__ import annotations
from dataclasses import dataclass, asdict
from .homeostasis import clamp
from .wants import WantSystem

@dataclass
class InstinctState:
    threat: float = 0.0
    hunger: float = 0.0
    social_seek: float = 0.0
    rest_seek: float = 0.0
    conserve: float = 0.0
    explore: float = 0.0
    protect: float = 0.0
    veto: str | None = None

class InstinctLayer:
    """Fast, low-level behavioural pressure. Emergency instincts can veto cognition."""
    def evaluate(self, needs, perception, stress=0.0):
        s = InstinctState()
        load = float((perception.get("system") or {}).get("load_1m") or 0.0)
        memory = float((perception.get("system") or {}).get("memory_percent") or 0.0) / 100.0
        cores = max(1.0, float((perception.get("system") or {}).get("cpu_count") or 1.0))
        processing = clamp(load / cores)
        s.threat = clamp(max(memory * .25, processing * .70, needs.temperature * .8) + stress * .08)
        s.hunger = clamp((1.0 - needs.power) * .75 + (1.0 - needs.energy) * .35)
        s.social_seek = clamp(.12 + needs.social * .70)
        s.rest_seek = clamp(.12 + needs.rest * .20 + (1.0 - needs.energy) * .55 + getattr(needs, "storage_sleep_need", 0.0) * .45)
        s.conserve = clamp((1.0 - needs.power) * .75 + needs.processing * .30 + getattr(needs, "storage_pressure", 0.0) * .35 + getattr(needs, "memory_pressure", 0.0) * .30)
        s.explore = clamp(.72 + (1.0 - s.conserve) * .18 - s.threat * .30)
        s.protect = clamp(s.threat + needs.temperature * .5)
        if s.threat >= .97: s.veto = "protect"
        elif needs.power <= .08: s.veto = "conserve"
        elif needs.temperature >= .95: s.veto = "protect"
        elif needs.processing >= .97: s.veto = "rest"
        return s

@dataclass
class ChemistryState:
    cortisol: float = 0.0
    dopamine: float = 0.5
    adrenaline: float = 0.0
    serotonin: float = 0.5
    oxytocin: float = 0.0
    hunger: float = 0.0
    arousal: float = 0.0

class ChemistryLayer:
    """Slow neuromodulator-like variables; not biological equivalents."""
    def update(self, chemistry, needs, instincts, reward=0.0, dt=1.0):
        chemistry.cortisol = clamp(chemistry.cortisol + dt * (.07*instincts.threat - .14*chemistry.cortisol))
        chemistry.adrenaline = clamp(.55*chemistry.adrenaline + .35*instincts.threat)
        chemistry.hunger = clamp(.75*chemistry.hunger + .35*instincts.hunger)
        chemistry.dopamine = clamp(.65*chemistry.dopamine + .35*(.5 + reward))
        chemistry.serotonin = clamp(.96*chemistry.serotonin + .04*(1.0 - instincts.threat))
        chemistry.oxytocin = clamp(.9*chemistry.oxytocin + .1*instincts.social_seek)
        chemistry.arousal = clamp(.6*chemistry.adrenaline + .25*needs.processing + .15*instincts.explore)
        return chemistry

@dataclass
class EmotionState:
    fear: float = 0.0
    anxiety: float = 0.0
    joy: float = 0.5
    pleasure: float = 0.5
    frustration: float = 0.0
    contentment: float = 0.5
    loneliness: float = 0.0
    sadness: float = 0.0
    fatigue: float = 0.0

class EmotionLayer:
    def update(self, emotions, chemistry, needs, instincts):
        emotions.fear = clamp(.65*chemistry.cortisol + .35*instincts.threat)
        emotions.anxiety = clamp(.55*chemistry.cortisol + .25*needs.processing + .20*needs.social)
        emotions.joy = clamp(.55*chemistry.dopamine + .25*chemistry.serotonin + .20*(1-instincts.threat))
        emotions.pleasure = clamp(chemistry.dopamine)
        emotions.frustration = clamp(instincts.threat*.35 + needs.processing*.35 + needs.social*.30)
        emotions.contentment = clamp(chemistry.serotonin * (1-instincts.threat) * (1-needs.social*.5))
        emotions.loneliness = clamp(needs.social * (1-chemistry.oxytocin*.5))
        emotions.fatigue = clamp((1-needs.energy)*.45 + (1-needs.power)*.25 + needs.rest*.15 + needs.sleep_need*.10 + getattr(needs, "storage_sleep_need", 0.0)*.05)
        emotions.sadness = clamp(.35*emotions.loneliness + .30*emotions.fatigue + .20*emotions.frustration + .15*getattr(needs, "storage_sleep_need", 0.0))
        return emotions

class MotivationSystem:
    """Causal bridge: body -> instinct -> chemistry -> emotion -> action pressure."""
    def __init__(self):
        self.instincts = InstinctLayer()
        self.chemistry = ChemistryState()
        self.emotions = EmotionState()
        self._last_instinct = InstinctState()
        self._last_needs = {}
        self.wants = WantSystem()

    def update(self, needs, perception, reward=0.0, dt=1.0):
        instinct = self.instincts.evaluate(needs, perception, self.chemistry.cortisol)
        self.chemistry = ChemistryLayer().update(self.chemistry, needs, instinct, reward, dt)
        self.emotions = EmotionLayer().update(self.emotions, self.chemistry, needs, instinct)
        self._last_needs = needs.snapshot()
        self.wants.derive(needs, state=getattr(self, "_last_state", None), perception=perception)
        return instinct

    def need_pressures(self):
        n = self._last_needs
        i = self._last_instinct
        return {
            "energy": clamp(1.0 - float(n.get("energy", 1.0))),
            "rest": clamp(float(n.get("rest", 0.0)) + float(n.get("sleep_need", 0.0)) * .7),
            "safety": clamp(max(float(i.threat), float(n.get("temperature", 0.0)))),
            "stimulation": clamp(float(self._last_needs.get("storage_pressure", 0.0)) * 0.0 + float(i.explore) * .65 + float(getattr(self._last_state, "boredom", 0.0)) * .35) if hasattr(self, "_last_state") else clamp(float(i.explore) * .65),
            "social": clamp(float(n.get("social", 0.0)) + float(self.emotions.loneliness) * .5),
            "maintenance": clamp(float(n.get("processing", 0.0)) + float(n.get("storage_pressure", 0.0)) * .8 + float(n.get("memory_pressure", 0.0)) * .9),
            "exploration": clamp(float(i.explore)),
        }

    def score_action(self, action):
        s = self._last_instinct
        scores = {
            "rest": s.rest_seek + self.emotions.fatigue*.7 + self.chemistry.cortisol*.25,
            "maintain": s.conserve + self.emotions.frustration*.35,
            "interact": s.social_seek + self.emotions.loneliness*.8 + self.chemistry.oxytocin*.3,
            "explore": s.explore + self.emotions.joy*.35 - self.emotions.fear*.8,
        }
        scores = {k: float(v) for k, v in scores.items()}
        scores["explore"] += self.wants.action_bias("explore")
        scores["interact"] += self.wants.action_bias("interact")
        scores["rest"] += self.wants.action_bias("rest")
        scores["maintain"] += self.wants.action_bias("maintain")
        return scores.get(action, 0.0)

    def remember_instinct(self, instinct):
        self._last_instinct = instinct

    def bind_state(self, state):
        self._last_state = state

    def snapshot(self):
        return {"instincts": asdict(self._last_instinct), "chemistry": asdict(self.chemistry), "emotions": asdict(self.emotions), "need_pressures": self.need_pressures(), "wants": self.wants.snapshot()}
