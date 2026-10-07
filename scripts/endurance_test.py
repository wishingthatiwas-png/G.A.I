"""G.A.I. V1 endurance observer. Does not control cognition; records health only."""
import json, time
from pathlib import Path
ROOT=Path('/mnt/gai'); STATE=ROOT/'state'; LOG=ROOT/'logs/endurance.jsonl'
RUNTIME=STATE/'runtime.json'; ACTIVE=STATE/'gai_active.json'; PID=STATE/'kernel.pid'
DURATION=float(__import__('os').environ.get('GAI_ENDURANCE_SECONDS','3600'))
INTERVAL=float(__import__('os').environ.get('GAI_ENDURANCE_INTERVAL','10'))
start=time.time(); LOG.parent.mkdir(parents=True,exist_ok=True)
with LOG.open('a') as f:
    while time.time()-start < DURATION:
        now=time.time()
        try: runtime=json.loads(RUNTIME.read_text())
        except Exception: runtime={}
        try: active=json.loads(ACTIVE.read_text())
        except Exception: active={}
        try: pid=int(PID.read_text().strip())
        except Exception: pid=None
        tick=runtime.get('tick',{})
        row={'ts':now,'elapsed_s':round(now-start,1),'active':bool(active.get('active')),'pid':pid,'target_fps':tick.get('target_fps'),'actual_fps':tick.get('actual_fps'),'metabolic_hz':tick.get('metabolic_hz'),'scheduler':runtime.get('scheduler',{}),'neural':runtime.get('neural_fabric',{}).get('population',{})}
        f.write(json.dumps(row,separators=(',',':'))+'\n'); f.flush()
        time.sleep(INTERVAL)
print(f'ENDURANCE_COMPLETE {DURATION:.0f}s')
