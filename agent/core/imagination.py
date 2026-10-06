from __future__ import annotations
import json,time,random
from pathlib import Path
from .cell import Cell
from .nervous import Event
ROOT=Path("/mnt/gai"); STATE=ROOT/"state"; OUT=STATE/"imagination.json"
class ImaginationPort(Cell):
    """Rudimentary internal simulation port connected to the CNS event bus."""
    def __init__(self,kernel):
        super().__init__("imagination",kernel.nervous,version="0.1.0",sleep_phases={"awake","dream"},critical=False)
        self.kernel=kernel; self.last=None
        self.listen("cognition.request",self.on_request,{"awake","dream"})
        self.listen("perception.observation",self.on_perception,{"awake","dream"})
        self.listen("reward.signal",self.on_reward,{"awake","dream"})
        self.listen("cognition.intention",self.on_intention,{"awake","dream"})
    def _scene(self,trigger="spontaneous"):
        state=self.kernel.state; drives=self.kernel.drives
        world=self.kernel.world.last_observation if hasattr(self.kernel.world,"last_observation") else {}
        visual=((world or {}).get("screen") or {}).get("visual") or {}
        curiosity=float(getattr(state,"curiosity",0) or 0); energy=float(getattr(self.kernel.core_needs,"energy",0) or 0)
        subjects=["the current desktop","a familiar workspace","an unexplored corner of the visual field","a future creative canvas"]
        subject=subjects[int(curiosity*10+energy*3)%len(subjects)]
        scene={"timestamp":time.time(),"trigger":trigger,"type":"internal_simulation","subject":subject,
               "visual_hint":{"brightness":visual.get("brightness"),"structure_change":visual.get("structure_change")},
               "predicted_motion":{"dx":round(random.uniform(-40,40),1),"dy":round(random.uniform(-25,25),1)},
               "affect":{"curiosity":curiosity,"energy":energy},
               "counterfactual":"If G.A.I. attends to this, something new may be learned or created.","safe":True}
        OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(scene,indent=2)); self.last=scene
        self.nervous.publish("imagination.scene",scene,source="imagination",priority="normal",novelty=min(1,curiosity))
        self.heartbeat({"last":"imagination.scene","trigger":trigger}); return scene
    def on_request(self,event:Event): self._scene("cognition_request")
    def on_perception(self,event:Event):
        if float(getattr(event,"novelty",0) or 0)>=.35:self._scene("novel_perception")
    def on_reward(self,event:Event):
        if float((event.payload or {}).get("value",0) or 0)>.2:self._scene("reward")
    def on_intention(self,event:Event): self._scene("cognitive_intention")
    def imagine(self,prompt=None): return self._scene(str(prompt or "manual"))
