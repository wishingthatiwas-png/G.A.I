from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
import json, time

ROOT=Path("/mnt/gai")

@dataclass
class Thought:
    timestamp: float
    kind: str
    text: str
    source: str
    intensity: float
    valence: float
    novelty: float
    drives: dict
    associations: list[str]

class ThoughtStream:
    """Cheap symbolic cognition. No language model runs here."""
    def __init__(self, kernel, limit=256):
        self.kernel=kernel
        self.items=deque(maxlen=limit)
        self.path=ROOT/"state/thoughts.jsonl"
        self.last_by_kind={}
        self.cooldowns={"presence":4.0,"perception":2.0,"prediction":2.0,"drive":3.0,"action":1.0}
        self._last_tick=0.0

    def _emit(self, kind,text,source,intensity=.2,valence=0.0,novelty=0.0,associations=None):
        now=time.time()
        last=self.last_by_kind.get(kind,0)
        if now-last < self.cooldowns.get(kind,1.0): return None
        t=Thought(now,kind,text,source,float(intensity),float(valence),float(novelty),
                  {"power":self.kernel.core_needs.power,"energy":self.kernel.core_needs.energy,
                   "rest":self.kernel.core_needs.rest,"processing":self.kernel.core_needs.processing},
                  associations or [])
        self.last_by_kind[kind]=now
        self.items.append(t)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open("a") as f: f.write(json.dumps(asdict(t),separators=(",",":"))+"\n")
        self.kernel.nervous.publish("thought.formed",asdict(t),source="cognition",
                                    priority="background",novelty=t.novelty)
        return t

    def tick(self):
        k=self.kernel
        now=time.time()
        # Persistent existence signal: one cheap symbolic thought, not generation.
        if now-self._last_tick >= self.cooldowns["presence"]:
            self._last_tick=now
            phase=k.lifecycle.state.phase.value
            emotion=k.motivation.emotions
            dominant=max(vars(emotion),key=vars(emotion).get) if emotion else "neutral"
            self._emit("presence",f"I am here. Phase is {phase}; I feel {dominant}.",
                       "homeostasis",.12,0.0,0.0)

    def perception(self,event):
        p=event.payload
        concepts=(p.get("concepts") or [])[:5]
        novelty=float(event.novelty)
        if novelty >= .25:
            detail=", ".join(concepts) if concepts else "something changed"
            self._emit("perception",f"I notice {detail}.","perception",
                       min(1,novelty),0.05,novelty,concepts)

    def prediction(self,event):
        value=float((event.payload or {}).get("value",0))
        if abs(value) >= .15:
            direction="different from what I expected" if value>0 else "closer to what I expected"
            self._emit("prediction",f"Something is {direction}.","prediction",
                       min(1,abs(value)), -abs(value)*.2,abs(value))

    def drive(self,event):
        k=self.kernel
        strongest=k.drives.strongest()
        if strongest:
            self._emit("drive",f"I want to {strongest}.","drives",
                       .25,0.05,0.05,[strongest])

    def action(self,event):
        a=(event.payload or {}).get("action","unknown")
        self._emit("action",f"I chose {a}.","control",.2,0.05,0.02,[a])

    def recent(self,limit=32):
        return [asdict(x) for x in list(self.items)[-limit:]]

    def snapshot(self):
        return {"count":len(self.items),"recent":self.recent(12)}
