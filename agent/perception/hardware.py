from __future__ import annotations
import subprocess
from pathlib import Path


def _run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
    except Exception:
        return None


def snapshot():
    camera = sorted(str(p) for p in Path('/dev').glob('video*'))
    gpu = _run(['nvidia-smi','--query-gpu=name,temperature.gpu,utilization.gpu,pstate,memory.used,memory.total','--format=csv,noheader'])
    return {'camera_devices': camera, 'nvidia': gpu}
