from __future__ import annotations
import json, subprocess, time, signal, os
from pathlib import Path
ROOT=Path('/mnt/gai'); PY=ROOT/'venvs/gai/bin/python'; AGENT=ROOT/'agent'
MODE=ROOT/'state/organ_mode.json'; SCENARIO=ROOT/'laboratory/current_scenario.json'
TRACE=ROOT/'state/v1_trace.jsonl'; OUT=ROOT/'laboratory/results.json'

def write(p,d): p.write_text(json.dumps(d,separators=(',',':')))

def run_kernel(seconds):
    p=subprocess.Popen([str(PY),str(AGENT/'main.py')],cwd=str(AGENT),env={**os.environ,'PYTHONPATH':str(AGENT)})
    time.sleep(seconds)
    p.send_signal(signal.SIGTERM)
    try: p.wait(timeout=2)
    except subprocess.TimeoutExpired: p.kill(); p.wait()
    subprocess.run(['pkill','-9','-f',str(AGENT/'main.py')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def trace_since(start):
    if not TRACE.exists(): return []
    rows=[]
    for line in TRACE.read_text().splitlines()[start:]:
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows

def scenario(name,steps,seconds=8):
    write(SCENARIO,{'name':name,'steps':steps})
    write(MODE,{'mode':'simulated','scenario':name,'timestamp':time.time()})
    start=len(TRACE.read_text().splitlines()) if TRACE.exists() else 0
    run_kernel(seconds)
    rows=trace_since(start)
    return {'name':name,'cycles':len(rows),
            'attention':[r.get('attention',{}) for r in rows],
            'actions':[r.get('action') for r in rows],
            'rewards':[r.get('outcome_reward',0) for r in rows]}

steady={'vision':{'temporal':{'salience':0.03,'onset':0.0,'velocity':0.01,'acceleration':0.0,'direction':'still'},'patterns':[{'colour':'green','shape':'quadrilateral','emotion':'safety','shape_affect':'stable'}]},'audio':{'available':True,'fresh':True,'signal':0.08,'rms':0.01,'auditory':{'transient':0.002,'attended_frequency':500}},'novelty':0.2}
move={'vision':{'temporal':{'salience':0.8,'onset':0.9,'velocity':0.7,'acceleration':0.6,'direction':'right'},'patterns':[{'colour':'yellow','shape':'triangle','emotion':'curiosity','shape_affect':'alert'}]},'audio':{'available':True,'fresh':True,'signal':0.12,'rms':0.02,'auditory':{'transient':0.004,'attended_frequency':750}},'novelty':0.95}
sound={'vision':{'temporal':{'salience':0.06,'onset':0.0,'velocity':0.01,'acceleration':0.0,'direction':'still'},'patterns':[{'colour':'gray','shape':'quadrilateral','emotion':'neutral','shape_affect':'stable'}]},'audio':{'available':True,'fresh':True,'signal':0.9,'rms':0.12,'auditory':{'transient':0.08,'attended_frequency':2000}},'novelty':0.85}

results=[
 scenario('visual_motion_capture',[steady,steady,move,move,steady],8),
 scenario('auditory_capture',[steady,steady,sound,sound,steady],8),
 scenario('repetition_habituation',[move]*8+[steady],10)
]
write(OUT,{'timestamp':time.time(),'experiments':results})
write(MODE,{'mode':'real','restored_after_lab':True,'timestamp':time.time()})
print(json.dumps({'experiments':[(x['name'],x['cycles']) for x in results]},indent=2))
