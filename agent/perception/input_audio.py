from __future__ import annotations
import json, math, os, struct, subprocess, threading, time
from pathlib import Path
from perception.auditory_organ import process as process_auditory, read_focus

ROOT=Path("/mnt/gai")
STATE=ROOT/"state/audio_input.json"

class AudioInputOrgan:
    """Microphone organ using the desktop's PipeWire graph."""
    def __init__(self, nervous, rate=48000, channels=2, capture_gain=0.03, chunk_seconds=1.0):
        self.nervous=nervous
        self.rate=rate; self.channels=channels
        self.capture_gain=capture_gain; self.chunk_bytes=int(rate*channels*2*chunk_seconds)
        self.running=False; self.thread=None; self.proc=None
        self.baseline=0.0; self.exposure=0

    def start(self):
        if self.running: return
        self.running=True
        self.thread=threading.Thread(target=self._run,daemon=True,name="gai-audio-input")
        self.thread.start()

    def stop(self):
        self.running=False
        p=self.proc
        if p:
            try: p.terminate()
            except Exception: pass

    def _publish(self, payload):
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(payload,separators=(",",":")))
        self.nervous.publish("audio.input",payload,source="audio.organ",priority="normal")

    def _run(self):
        env=dict(os.environ)
        env.setdefault("XDG_RUNTIME_DIR","/run/user/1000")
        cmd=["pw-record","--rate",str(self.rate),"--channels",str(self.channels),
             "--format","s16","--volume",str(self.capture_gain),"-"]
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                       env=env,start_new_session=True)
            while self.running and self.proc.stdout:
                data=self.proc.stdout.read(self.chunk_bytes)
                if not data: break
                samples=struct.unpack("<%dh"%(len(data)//2),data)
                if not samples: continue
                rms=math.sqrt(sum(x*x for x in samples)/len(samples))/32768.0
                peak=max(abs(x) for x in samples)/32768.0
                self.exposure+=1
                self.baseline += 0.05*(rms-self.baseline)
                signal=min(1.0,rms/max(0.001,self.baseline+0.01))
                payload={"timestamp":time.time(),"available":True,"rms":round(rms,6),"peak":round(peak,6),
                         "baseline_rms":round(self.baseline,6),"signal":round(signal,6),
                         "rate":self.rate,"channels":self.channels,"capture_gain":self.capture_gain}
                try:
                    auditory=process_auditory(samples,self.rate,self.channels,read_focus())
                    payload["auditory"]=auditory
                except Exception as exc:
                    payload["auditory"]={"available":False,"error":str(exc)}
                self._publish(payload)
        except Exception as exc:
            self._publish({"timestamp":time.time(),"available":False,"error":str(exc)})
        finally:
            p=self.proc
            if p:
                try: p.terminate()
                except Exception: pass
            self.proc=None
            self.running=False
