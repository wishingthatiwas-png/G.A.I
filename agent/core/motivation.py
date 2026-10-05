from __future__ import annotations
from dataclasses import dataclass, asdict
from .homeostasis import clamp

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
        s.threat = clamp(max(memory * .7, load / 2.0) + stress * .35)
        s.hunger = clamp((1.0 - needs.energy) * .75 + (1.0 - needs.power) * .55)
        s.social_seek = clamp(needs.social)
        s.rest_seek = clamp(needs.rest + (1.0 - needs.energy) * .25)
        s.conserve = clamp((1.0 - needs.power) * .9 + needs.processing * .45)
        s.explore = clamp(.55 + (1.0 - s.conserve) * .25 - s.threat * .65)
        s.protect = clamp(s.threat + needs.temperature * .5)

        if s.threat >= .90:
            s.veto = "protect"
        elif needs.power <= .08:
            s.veto = "conserve"
        elif needs.temperature >= .95:
            s.veto = "protect"
        elif needs.processing >= .97:
            s.veto = "rest"
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
        chemistry.cortisol = clamp(chemistry.cortisol + dt * (.18*instincts.threat - .04*chemistry.cortisol))
        chemistry.adrenaline = clamp(.65*chemistry.adrenaline + .55*instincts.threat)
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
        emotions.fatigue = clamp((1-needs.energy)*.6 + needs.rest*.4)
        return emotions

class MotivationSystem:
    """Causal bridge: body -> instinct -> chemistry -> emotion -> action pressure."""
    def __init__(self):
        self.instincts = InstinctLayer()
        self.chemistry = ChemistryState()
        self.emotions = EmotionState()
        self._last_instinct = InstinctState()

    def update(self, needs, perception, reward=0.0, dt=1.0):
        instinct = self.instincts.evaluate(needs, perception, self.chemistry.cortisol)
        self.chemistry = ChemistryLayer().update(self.chemistry, needs, instinct, reward, dt)
        self.emotions = EmotionLayer().update(self.emotions, self.chemistry, needs, instinct)
        return instinct

    def score_action(self, action):
        s = self._last_instinct
        scores = {
            "rest": s.rest_seek + self.emotions.fatigue*.7 + self.chemistry.cortisol*.25,
            "maintain": s.conserve + self.emotions.frustration*.35,
            "interact": s.social_seek + self.emotions.loneliness*.8 + self.chemistry.oxytocin*.3,
            "explore": s.explore + self.emotions.joy*.35 - self.emotions.fear*.8,
        }
        return scores.get(action, 0.0)

    def remember_instinct(self, instinct):
        self._last_instinct = instinct

    def snapshot(self):
        return {"instincts": asdict(self._last_instinct),
                "chemistry": asdict(self.chemistry),
                "emotions": asdict(self.emotions)}
