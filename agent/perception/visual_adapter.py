from __future__ import annotations
import hashlib, json, os, subprocess, time
from pathlib import Path
from PIL import Image, ImageStat
from perception.sight_focus import read as read_focus

ROOT=Path("/mnt/gai")
SCREEN=ROOT/"state/viewfinder.png"
GAZE=ROOT/"state/gaze.json"

def _active_window():
    try:
        env=dict(os.environ); env.setdefault("DISPLAY", ":0"); env.setdefault("XAUTHORITY", "/home/null/.Xauthority")
        wid=subprocess.check_output(["xprop","-root","_NET_ACTIVE_WINDOW"],text=True,timeout=1,env=env).strip()
        wid=wid.split()[-1]
        raw=subprocess.check_output(["xprop","-id",wid,"_NET_WM_NAME","WM_CLASS"],text=True,timeout=1,env=env)
        return raw.strip()
    except Exception:
        return None

def describe(path=SCREEN):
    result={"available":False}
    try:
        im=Image.open(path).convert("RGB")
        w,h=im.size
        thumb=im.resize((16,9))
        pix=list(thumb.get_flattened_data())
        avg=tuple(round(sum(p[i] for p in pix)/len(pix)) for i in range(3))
        brightness=sum(avg)/3
        quadrants=[]
        for yy in range(3):
            row=[]
            for xx in range(4):
                box=(xx*w//4,yy*h//3,(xx+1)*w//4,(yy+1)*h//3)
                q=ImageStat.Stat(im.crop(box))
                row.append(round(sum(q.mean)/3))
            quadrants.append(row)
        # Coarse visual structure: brightness changes between adjacent grid cells.
        edge=0.0
        for yy in range(3):
            for xx in range(3):
                edge += abs(quadrants[yy][xx]-quadrants[yy][xx+1])
        for yy in range(2):
            for xx in range(4):
                edge += abs(quadrants[yy][xx]-quadrants[yy+1][xx])
        gaze={}
        try: gaze=json.loads(GAZE.read_text())
        except Exception: pass
        focus=read_focus()
        gx=max(0,min(1,float(focus.get("x",gaze.get("x",.5))))); gy=max(0,min(1,float(focus.get("y",gaze.get("y",.5)))))
        radius=max(.08,min(.35,float(focus.get("radius",.18))))
        fw=max(24,int(w*radius*2)); fh=max(24,int(h*radius*2))
        left=max(0,min(w-fw,int(gx*w-fw/2))); top=max(0,min(h-fh,int(gy*h-fh/2)))
        box=(left,top,left+fw,top+fh)
        crop=im.crop(box) if box[2]>box[0] and box[3]>box[1] else im
        cs=ImageStat.Stat(crop)
        result.update({
            "available":True,"width":w,"height":h,
            "average_rgb":avg,"brightness":round(brightness,1),
            "brightness_grid":quadrants,"structure_change":round(edge,1),
            "gaze_region_rgb":tuple(round(x) for x in cs.mean),
            "screen_hash":hashlib.sha256(path.read_bytes()).hexdigest()[:16],
            "active_window":_active_window(),
            "gaze":{"x":gx,"y":gy,"target":gaze.get("target"),"reason":gaze.get("reason")}
        })
    except Exception as exc:
        result["error"]=str(exc)
    return result
