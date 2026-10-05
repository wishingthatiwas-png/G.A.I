from __future__ import annotations
from pathlib import Path
import json,time
from memory.engram_decay import decay

QUEUE=Path("/mnt/gai/memory/dream_queue.jsonl")
REPORT=Path("/mnt/gai/memory/dream_report.json")

class DreamEngine:
    """Offline consolidation + selection. No evolutionary mutation occurs while awake."""
    def __init__(self,evolution=None):
        QUEUE.parent.mkdir(parents=True,exist_ok=True); self.evolution=evolution

    def queue(self,event):
        with QUEUE.open("a") as f: f.write(json.dumps({"timestamp":time.time(),"event":event})+"\n")

    def consolidate(self,associative,learner):
        if not QUEUE.exists(): return {"events":0,"changes":0,"evolution":None}
        events=[json.loads(x)["event"] for x in QUEUE.read_text().splitlines() if x.strip()]
        changes=0
        decay_rate=self.evolution.genes["memory_decay"].value if self.evolution else 0.02
        pruned=decay(associative,decay_rate)
        for e in events[-500:]:
            stimuli=e.get("stimuli",[])
            if stimuli:
                associative.fire(stimuli,emotions=e.get("emotions",{}),
                    context={"dream_replay":True},reward=float(e.get("reward",0))); changes+=1
        evo=self.evolution.dream_select(events[-500:],population=8) if self.evolution else None
        report={"timestamp":time.time(),"events":len(events),"changes":changes,"evolution":evo,
                "outcome_models":{k:vars(v) for k,v in learner.models.items()}}
        REPORT.write_text(json.dumps(report,indent=2)); QUEUE.write_text("")
        return report
