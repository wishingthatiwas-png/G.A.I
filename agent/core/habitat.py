from __future__ import annotations
import json, time
from pathlib import Path
ROOT=Path("/mnt/gai"); STATE=ROOT/"state"; PATH=STATE/"digital_habitat.json"; EVENTS=STATE/"habitat_events.jsonl"
DEFAULT={"version":1,"objects":[
{"id":"curiosity_object","kind":"orb","x":.70,"y":.30,"size":.10,"state":"quiet","colour":"cyan","energy":.7,"changes":0},
{"id":"light_switch","kind":"switch","x":.20,"y":.28,"size":.07,"state":"off","colour":"amber","energy":.4,"changes":0},
{"id":"paint_pad","kind":"pad","x":.36,"y":.68,"size":.12,"state":"ready","colour":"violet","energy":.6,"changes":0},
{"id":"sound_box","kind":"speaker","x":.68,"y":.72,"size":.09,"state":"quiet","colour":"green","energy":.5,"changes":0},
{"id":"memory_stone","kind":"stone","x":.84,"y":.55,"size":.08,"state":"stable","colour":"blue","energy":.3,"changes":0}],"last_event":None,"timestamp":0.0}
class DigitalHabitat:
    def __init__(self,path:Path=PATH):
        self.path=path; self.state=self._load()
    def _load(self):
        try:
            obj=json.loads(self.path.read_text())
            if isinstance(obj,dict) and isinstance(obj.get("objects"),list): return obj
        except Exception: pass
        self.state=json.loads(json.dumps(DEFAULT)); self.save(); return self.state
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); self.state["timestamp"]=time.time()
        self.path.write_text(json.dumps(self.state,indent=2))
    def objects(self): return list(self.state.get("objects",[]))
    def get(self,object_id): return next((o for o in self.state["objects"] if o.get("id")==object_id),None)
    def emit(self,kind,object_id=None,data=None):
        event={"timestamp":time.time(),"kind":kind,"object":object_id,"data":data or {}}
        self.state["last_event"]=event; EVENTS.parent.mkdir(parents=True,exist_ok=True)
        with EVENTS.open("a") as f: f.write(json.dumps(event,separators=(",",":"))+"\n")
        self.save(); return event
    def interact(self,object_id):
        obj=self.get(object_id)
        if not obj: return {"success":False,"reason":"unknown_object","object":object_id,"reward":-.1}
        pairs={"curiosity_object":("active","quiet"),"light_switch":("on","off"),"paint_pad":("painted","ready"),"sound_box":("playing","quiet"),"memory_stone":("warm","stable")}
        on,off=pairs.get(object_id,(obj.get("state","active"),obj.get("state","active")))
        obj["state"]=off if obj.get("state")==on else on; obj["changes"]=int(obj.get("changes",0))+1
        reward=.65; event=self.emit("interaction",object_id,{"new_state":obj["state"],"changes":obj["changes"],"reward":reward})
        return {"success":True,"object":object_id,"new_state":obj["state"],"changes":obj["changes"],"reward":reward,"event":event}
