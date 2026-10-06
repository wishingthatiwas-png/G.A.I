from __future__ import annotations
import json
import time
from memory.engram_decay import decay


class DreamEngine:
    """Offline consolidation coordinator.

    Persistent experience storage belongs to MemoryPipeline. Dream only keeps a
    small in-process replay window for associative replay and evolution, so
    there is one memory queue rather than competing sleep stores.
    """
    def __init__(self, evolution=None):
        self.evolution = evolution
        self.replay: list[dict] = []
        self.last_report = None

    def queue(self, event):
        if event:
            self.replay.append(dict(event))
            self.replay = self.replay[-500:]

    def consolidate(self, associative, learner):
        events = list(self.replay[-500:])
        changes = 0
        if events:
            decay_rate = self.evolution.genes["memory_decay"].value if self.evolution else 0.02
            decay(associative, decay_rate)
            for event in events:
                stimuli = event.get("stimuli", [])
                if stimuli:
                    associative.fire(
                        stimuli,
                        emotions=event.get("emotions", {}),
                        context={"dream_replay": True},
                        reward=float(event.get("reward", 0)),
                    )
                    changes += 1

        evo = self.evolution.dream_select(events, population=8) if self.evolution else None
        report = {
            "timestamp": time.time(),
            "events": len(events),
            "changes": changes,
            "evolution": evo,
            "experience_models": learner.snapshot(),
        }
        self.last_report = report
        self.replay.clear()
        return report
