from pathlib import Path
import json, time
ROOT=Path("/mnt/gai"); STATE=ROOT/"state"; FOCUS=STATE/"sight_focus.json"
DEFAULT={"mode":"in","eyes_open":0.72,"x":0.50,"y":0.50,"radius":0.18,"target":"virtual_habitat","reason":"default_inward_virtual_attention","timestamp":0.0}
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,float(v)))
def read():
    try: d=json.loads(FOCUS.read_text())
    except Exception: d={}
    out=dict(DEFAULT); out.update(d); out["mode"]="out" if str(out.get("mode"))=="out" else "in"; out["x"]=_clamp(out.get("x",.5)); out["y"]=_clamp(out.get("y",.5)); out["radius"]=_clamp(out.get("radius",.18),.08,.35); out["eyes_open"]=_clamp(out.get("eyes_open",.88)); return out
def set_focus(mode=None,x=None,y=None,radius=None,target=None,reason="attention"):
    d=read()
    if mode is not None: d["mode"]="out" if str(mode).lower()=="out" else "in"
    if x is not None: d["x"]=_clamp(x)
    if y is not None: d["y"]=_clamp(y)
    if radius is not None: d["radius"]=_clamp(radius,.08,.35)
    if target is not None: d["target"]=str(target)
    d["reason"]=reason; d["eyes_open"]=0.88 if d["mode"]=="out" else 0.72; d["timestamp"]=time.time()
    FOCUS.parent.mkdir(parents=True,exist_ok=True); FOCUS.write_text(json.dumps(d,separators=(",",":"))); return d
