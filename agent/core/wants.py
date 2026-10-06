from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(v)))


@dataclass
class Want:
    name: str
    strength: float
    target: str
    action_affinity: str
    reason: str


class WantSystem:
    """Short-lived desired outcomes derived from needs and the current situation.

    Wants bias motivation; they never issue hardware or action commands.
    """

    def __init__(self):
        self.wants: list[Want] = []

    def derive(self, needs, state=None, perception=None, memory_hits=None):
        perception = perception or {}
        memory_hits = memory_hits or []
        senses = perception.get("senses") or perception
        vision = senses.get("vision") or {}
        audio = senses.get("audio") or {}
        novelty = clamp(float(vision.get("sensory_novelty", 0.0) or 0.0))
        patterns = vision.get("patterns") or []
        rms = clamp(float((audio.get("auditory") or {}).get("rms", audio.get("rms", 0.0)) or 0.0) * 8.0)
        boredom = clamp(float(getattr(state, "boredom", 0.0))) if state is not None else 0.0

        candidates = [
            Want("recover_energy", clamp(float(needs.rest) + float(needs.sleep_need) * .7),
                 "body", "rest", "rest pressure"),
            Want("maintain_body", clamp(float(needs.processing) * .55 + float(getattr(needs, "storage_pressure", 0.0)) * .35 +
                                       float(getattr(needs, "memory_pressure", 0.0)) * .45),
                 "body", "maintain", "maintenance pressure"),
            Want("seek_interaction", clamp(float(needs.social) * .8 + .15),
                 "user_or_object", "interact", "social/interaction need"),
            Want("explore_novelty", clamp(float(getattr(needs, "rest", 0.0)) * 0.0 +
                                          novelty * .75 + boredom * .55 + float(getattr(needs, "energy", 1.0)) * .08),
                 "novel_environment", "explore", "novelty/boredom"),
            Want("investigate_sound", clamp(rms * .75 + novelty * .15),
                 "sound_event", "listen", "auditory salience"),
        ]
        if patterns:
            candidates.append(Want("understand_pattern", clamp(.35 + .08 * len(patterns) + novelty * .35),
                                   "visual_pattern", "look", "perceptual pattern"))
        if memory_hits:
            candidates.append(Want("revisit_memory", clamp(.18 + .10 * min(4, len(memory_hits))),
                                   "relevant_memory", "look", "relevant remembered experience"))

        self.wants = sorted(
            [w for w in candidates if w.strength > .05],
            key=lambda w: w.strength,
            reverse=True,
        )[:8]
        return self.wants

    def action_bias(self, action: str) -> float:
        return clamp(sum(w.strength for w in self.wants if w.action_affinity == action))

    def strongest(self):
        return asdict(self.wants[0]) if self.wants else None

    def snapshot(self):
        return {"wants": [asdict(w) for w in self.wants], "strongest": self.strongest()}
