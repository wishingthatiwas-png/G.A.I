from __future__ import annotations
import json, time
from pathlib import Path
from perception.sight_focus import read as read_focus

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'
SCREEN=STATE/'screen_stream.jpg'; CAMERA=STATE/'camera_stream.jpg'; SOURCES=STATE/'camera_organ.json'

def _meta(path):
    try:
        st=path.stat()
        return {'path':str(path),'available':True,'timestamp':st.st_mtime,'age_seconds':round(max(0.0,time.time()-st.st_mtime),3)}
    except Exception:
        return {'path':str(path),'available':False}

def snapshot():
    """Read persistent sensory-stream metadata; never capture a screenshot here."""
    focus=read_focus()
    return {
        'display_stream':_meta(SCREEN),
        'camera_stream':_meta(CAMERA),
        'camera_organ': _read_camera(),
        'focus': focus,
        'persistent': True,
        'captured': True,
        'timestamp': time.time(),
    }

def _read_camera():
    try: return json.loads(SOURCES.read_text())
    except Exception: return {'available':False}
