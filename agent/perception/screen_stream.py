from __future__ import annotations
import os, subprocess, threading, time
from pathlib import Path

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'
FRAME=STATE/'screen_stream.jpg'
PID=STATE/'screen_stream.pid'
ENV=dict(os.environ); ENV.setdefault('DISPLAY',':0'); ENV.setdefault('XAUTHORITY','/home/null/.Xauthority')

def main():
    STATE.mkdir(parents=True,exist_ok=True); PID.write_text(str(os.getpid()))
    cmd=[
        'ffmpeg','-loglevel','error','-f','x11grab','-framerate','5',
        '-i',':0.0','-vf','scale=640:360','-q:v','8',
        '-f','mjpeg','pipe:1'
    ]
    proc=subprocess.Popen(cmd,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
    try:
        buf=bytearray()
        while True:
            chunk=proc.stdout.read(16384)
            if not chunk: break
            buf.extend(chunk)
            while True:
                start=buf.find(b'\xff\xd8')
                if start<0: 
                    if len(buf)>2_000_000: del buf[:-2_000_000]
                    break
                end=buf.find(b'\xff\xd9',start+2)
                if end<0:
                    if start>0: del buf[:start]
                    break
                frame=bytes(buf[start:end+2]); del buf[:end+2]
                tmp=FRAME.with_suffix('.tmp.jpg')
                tmp.write_bytes(frame)
                os.replace(tmp,FRAME)
    except Exception:
        pass
    finally:
        try: proc.terminate()
        except Exception: pass
        try: proc.wait(timeout=1)
        except Exception: 
            try: proc.kill()
            except Exception: pass
        try: PID.unlink()
        except FileNotFoundError: pass

if __name__=='__main__':
    main()
