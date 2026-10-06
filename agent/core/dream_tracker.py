from __future__ import annotations
import json
import time
from pathlib import Path

ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
LOG = STATE / "dream_tracker.jsonl"
SNAPSHOT = STATE / "dream_tracker.json"

class DreamTracker:
    """Observer for sleep/dream episodes. It never controls lifecycle or waking."""
    def __init__(self):
        self.events = []
        self.session_id = None
        try:
            if SNAPSHOT.exists():
                obj=json.loads(SNAPSHOT.read_text())
                self.events=list(obj.get("events", []))[-500:]
                self.session_id=obj.get("session_id")
        except Exception:
            self.events=[]

    def event(self, kind, session=None, **data):
        sid = session.id if session else self.session_id
        if sid:
            self.session_id = sid
        item = {"timestamp": time.time(), "session_id": sid, "event": kind, **data}
        self.events.append(item)
        self.events = self.events[-500:]
        STATE.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps(item, separators=(",", ":")) + "\n")
        SNAPSHOT.write_text(json.dumps({
            "session_id": self.session_id,
            "events": self.events[-100:],
            "event_count": len(self.events),
            "updated_at": time.time(),
        }, indent=2))
        return item

    def stage(self, stage, session=None, **data):
        return self.event("stage", session, stage=stage, **data)

    def snapshot(self):
        return {
            "session_id": self.session_id,
            "event_count": len(self.events),
            "last_event": self.events[-1] if self.events else None,
        }
