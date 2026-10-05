from __future__ import annotations
from collections import deque
from .cell import Cell

class WorkingMemoryCell(Cell):
    """Short-lived event workspace feeding language and higher cognition."""
    PATTERNS=("perception.observation","drive.update","prediction.error",
              "control.decision","action.request","reward.signal",
              "lifecycle.transition")

    def __init__(self,nervous,limit=128):
        super().__init__("working_memory",nervous,sleep_phases={"awake","pre_sleep","dream","wake"})
        self.items=deque(maxlen=limit)
        for pattern in self.PATTERNS: self.listen(pattern,self.receive)

    def receive(self,event):
        payload=dict(event.payload)
        self.items.append({"kind":event.kind,"source":event.source,
                           "priority":event.priority,"timestamp":event.timestamp,
                           "correlation_id":event.correlation_id,
                           "provenance":event.provenance,"confidence":event.confidence,
                           "novelty":event.novelty,"payload":payload})
        self.heartbeat({"items":len(self.items),"last":event.kind})

    def recall(self,limit=32):
        return list(self.items)[-limit:]

    def salient(self,limit=16):
        items=list(self.items)
        items.sort(key=lambda x:(-x["novelty"],x["priority"],-x["timestamp"]))
        return items[:limit]

    def snapshot(self):
        return {"items":len(self.items),"recent":self.recall(8),
                "salient":self.salient(8),"state":self.state}
