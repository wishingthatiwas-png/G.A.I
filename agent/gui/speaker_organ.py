from __future__ import annotations
import json, math, os, struct, time, wave
from pathlib import Path

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'; REQUEST=STATE/'speaker_request.json'; BODY=STATE/'body_output.json'; STATUS=STATE/'speaker_organ.json'
TONES={'curiosity':660.0,'happiness':784.0,'contentment':523.0,'fear':220.0,'stress':180.0,'fatigue':260.0,'boredom':330.0,'neutral':440.0}

def play(req):
    emotion=str(req.get('emotion','neutral'))
    f=float(req.get('frequency',TONES.get(emotion,440.0)))
    dur=max(.04,min(1.5,float(req.get('duration',.12))))
    amp=max(.01,min(.12,float(req.get('amplitude',.08))))
    n=int(44100*dur); frames=bytearray()
    for i in range(n):
        t=i/44100.0; env=min(1.0,t/.018,(dur-t)/.035)
        x=int(32767*amp*max(0,env)*math.sin(2*math.pi*f*t)); frames+=struct.pack('<hh',x,x)
    out=STATE/'audio_output'/'speaker_organ.wav'; out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(44100); wf.writeframes(frames)
    env=dict(os.environ); env.setdefault('XDG_RUNTIME_DIR','/run/user/1000')
    ok=os.system(f"pw-play '{out}' >/dev/null 2>&1") == 0
    now=time.time()
    STATUS.write_text(json.dumps({'persistent':True,'last':now,'playing':ok,'audio_active':ok,'mode':'affective_tone','emotion':emotion,'frequency':f,'duration':dur},separators=(',',':')))
    b=json.loads(BODY.read_text()) if BODY.exists() else {}
    b.update({'timestamp':now,'audio_active':ok,'mode':'affective_tone','emotion':emotion,'frequency':f,'duration':dur,'rms':amp/math.sqrt(2) if ok else 0,'peak':amp if ok else 0,'text':''})
    BODY.write_text(json.dumps(b,separators=(',',':')))

def main():
    STATUS.write_text(json.dumps({'persistent':True,'started':time.time(),'playing':False,'mode':'affective_tone'}))
    last=0
    while True:
        try:
            req=json.loads(REQUEST.read_text()); ts=float(req.get('timestamp',0))
            if ts>last: last=ts; play(req)
        except Exception: pass
        time.sleep(.08)

if __name__=='__main__': main()
