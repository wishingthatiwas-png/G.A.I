from __future__ import annotations
import os, subprocess, time
from pathlib import Path

STATE=Path('/mnt/gai/state'); PID=STATE/'display_guard.pid'
ENV=dict(os.environ); ENV.setdefault('DISPLAY',':0'); ENV.setdefault('XAUTHORITY','/home/null/.Xauthority')

def enforce():
    settings=[
        ['gsettings','set','org.cinnamon.desktop.session','idle-delay','0'],
        ['gsettings','set','org.cinnamon.desktop.screensaver','lock-enabled','false'],
        ['gsettings','set','org.cinnamon.settings-daemon.plugins.power','sleep-display-ac','0'],
        ['gsettings','set','org.cinnamon.settings-daemon.plugins.power','sleep-inactive-ac-timeout','0'],
        ['gsettings','set','org.cinnamon.settings-daemon.plugins.power','sleep-inactive-ac-type','nothing'],
    ]
    for cmd in settings:
        try: subprocess.run(cmd,env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
        except Exception: pass
    try:
        subprocess.run(['xset','s','off'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
        subprocess.run(['xset','-dpms'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
        subprocess.run(['xset','s','noblank'],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
    except Exception: pass

def main():
    STATE.mkdir(parents=True,exist_ok=True); PID.write_text(str(os.getpid()))
    try:
        while True:
            enforce(); time.sleep(15)
    finally:
        try: PID.unlink()
        except FileNotFoundError: pass

if __name__=='__main__': main()
