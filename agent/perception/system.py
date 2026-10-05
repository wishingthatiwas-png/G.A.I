from __future__ import annotations
import os, platform, shutil, time
from pathlib import Path


def _meminfo():
    vals = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        k, v = line.split(':', 1)
        vals[k] = int(v.strip().split()[0]) * 1024
    return vals


def snapshot():
    mem = _meminfo()
    load = os.getloadavg()
    return {
        'timestamp': time.time(),
        'hostname': platform.node(),
        'kernel': platform.release(),
        'cpu_count': os.cpu_count(),
        'load_1m': load[0],
        'memory_total': mem.get('MemTotal'),
        'memory_available': mem.get('MemAvailable'),
        'swap_total': mem.get('SwapTotal'),
        'swap_free': mem.get('SwapFree'),
        'disk_free_gai': shutil.disk_usage('/mnt/gai').free,
    }
