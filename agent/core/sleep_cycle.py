from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import uuid
from pathlib import Path

STATE=Path("/mnt/gai/state")
PERSIST=STATE/"sleep_session.json"

class SleepStage(str, Enum):
    AWAKE="awake"
    DROWSY="drowsy"
    PRE_SLEEP="pre_sleep"
    SLEEP_ENTRY="sleep_entry"
    DEEP_SLEEP="deep_sleep"
    DREAM="dream"
    SLEEP_EXIT="sleep_exit"
    WAKE_RECOVERY="wake_recovery"

@dataclass
class SleepSession:
    id: str
    started_at: float
    stage: str = SleepStage.AWAKE.value
    cycle: int = 0
    wake_requested: bool = False
    wake_reason: str = ""
    consolidation_complete: bool = False
    physical: bool = False
    suspend_attempted: bool = False
    suspend_completed: bool | None = None
    completed: bool = False
    completed_at: float = 0.0

class SleepCycle:
    """Physiological sleep state; Linux suspend is an external body event."""
    def __init__(self):
        self.session: SleepSession|None=None
        self.history=[]
        self._last_transition=time.time()
        self._load()

    def _load(self):
        try:
            obj=json.loads(PERSIST.read_text())
            s=obj.get("session")
            if s and not s.get("completed"):
                self.session=SleepSession(**s)
            self.history=obj.get("history", [])[-20:]
        except Exception:
            pass

    def _save(self):
        STATE.mkdir(parents=True,exist_ok=True)
        PERSIST.write_text(json.dumps({
            "session":asdict(self.session) if self.session else None,
            "history":self.history[-20:],
            "updated_at":time.time()
        },indent=2))

    @property
    def stage(self):
        return self.session.stage if self.session else SleepStage.AWAKE.value

    def start(self,reason="sleep",physical=False):
        if self.session and not self.session.completed:
            return self.session
        self.session=SleepSession(
            id=time.strftime("%Y%m%d-%H%M%S")+"-"+uuid.uuid4().hex[:8],
            started_at=time.time(), stage=SleepStage.PRE_SLEEP.value,
            physical=bool(physical))
        self._last_transition=time.time()
        self._save()
        return self.session

    def request_wake(self,reason="wake"):
        if not self.session or self.session.completed:
            return None
        self.session.wake_requested=True
        self.session.wake_reason=reason
        self._save()
        return self.session

    def enter(self,stage):
        if not self.session:
            return None
        self.session.stage=str(stage)
        self._last_transition=time.time()
        self._save()
        return self.session

    def mark_suspend(self,attempted=True,completed=None):
        if self.session:
            self.session.suspend_attempted=attempted
            self.session.suspend_completed=completed
            self._save()

    def mark_consolidated(self):
        if self.session:
            self.session.consolidation_complete=True
            self._save()

    def can_wake(self):
        if not self.session or not self.session.wake_requested:
            return False
        return self.session.consolidation_complete or self.stage in (
            SleepStage.SLEEP_EXIT.value, SleepStage.WAKE_RECOVERY.value)

    def finish(self):
        if not self.session:
            return None
        self.session.stage=SleepStage.AWAKE.value
        self.session.completed=True
        self.session.completed_at=time.time()
        self.history.append(asdict(self.session))
        self.history=self.history[-20:]
        result=self.session
        self._save()
        return result

    def snapshot(self):
        return {
            "active":bool(self.session and not self.session.completed),
            "session":asdict(self.session) if self.session else None,
            "history_count":len(self.history),
            "last_completed":self.history[-1] if self.history else None,
        }
