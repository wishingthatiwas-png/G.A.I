from __future__ import annotations
import subprocess

def snapshot():
    try:
        out = subprocess.check_output(['bash','-lc','xrandr --current 2>/dev/null | head -1'], text=True, timeout=2).strip()
    except Exception:
        out = None
    return {'display': out}
