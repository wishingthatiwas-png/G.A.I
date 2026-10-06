#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path

ROOT=Path('/mnt/gai'); STATE=ROOT/'state'
LID=Path('/proc/acpi/button/lid/LID0/state')
REQUEST=STATE/'physical_lifecycle_request.json'
STATUS=STATE/'lid_sleep_bridge.json'
TRACKER=STATE/'dream_tracker.jsonl'
POLL=.25

def lid_open():
    try: return 'open' in LID.read_text().lower()
    except Exception: return True

def write_request(command, reason):
    REQUEST.write_text(json.dumps({
        'command':command, 'reason':reason, 'timestamp':time.time(),
        'source':'physical_lid', 'non_vetoable':True
    },separators=(',',':')))

def write_status(state, **extra):
    obj={'state':state,'timestamp':time.time(),**extra}
    STATUS.write_text(json.dumps(obj,separators=(',',':')))

def tracker_event(kind, session_id=None, **data):
    item={'timestamp':time.time(),'session_id':session_id,'event':kind,**data}
    STATE.mkdir(parents=True,exist_ok=True)
    with TRACKER.open('a') as f:
        f.write(json.dumps(item,separators=(',',':'))+'\n')

def suspend_result(started, rc):
    elapsed=time.time()-started
    try:
        logs=subprocess.run(
            ['journalctl','-k','--since',f'@{started-1:.3f}','--no-pager'],
            capture_output=True,text=True,timeout=2
        ).stdout
    except Exception:
        logs=''
    nvidia_failed=('failed to suspend' in logs or 'nv_pmops_suspend' in logs or 'pci_pm_suspend returns -5' in logs)
    entry='PM: suspend entry' in logs
    exit_seen='PM: suspend exit' in logs
    # A real suspend/resume is normally orders of magnitude longer than the
    # immediate NVIDIA failure path. Kernel evidence is preferred when present.
    completed=entry and exit_seen and not nvidia_failed and elapsed >= 3.0
    return {
        'command_rc':int(rc),
        'elapsed_seconds':round(elapsed,3),
        'kernel_suspend_entry':entry,
        'kernel_suspend_exit':exit_seen,
        'nvidia_suspend_failure':nvidia_failed,
        'completed':completed,
    }

def main():
    if '--worker' not in os.sys.argv:
        cmd=['systemd-inhibit','--what=handle-lid-switch','--mode=block',
             '--why=G.A.I. physiological sleep transition','--who=G.A.I.',
             '/bin/sh','-c','exec /mnt/gai/venvs/gai/bin/python /mnt/gai/agent/core/lid_guard.py --worker']
        os.execvp(cmd[0],cmd)

    previous=lid_open()
    write_status('open' if previous else 'closed')
    while True:
        current=lid_open()
        if previous and not current:
            write_status('closing')
            write_request('sleep','physical lid closed')
            deadline=time.time()+8
            phase=''
            while time.time()<deadline:
                try:
                    snap=json.loads((STATE/'runtime.json').read_text())
                    phase=str((snap.get('lifecycle') or {}).get('phase',''))
                except Exception:
                    phase=''
                if phase in ('dream','pre_sleep'):
                    break
                time.sleep(.15)

            write_status('sleeping', lifecycle_phase=phase)
            started=time.time()
            result=subprocess.run(['systemctl','suspend'],check=False).returncode
            outcome=suspend_result(started,result)
            session_id=None
            try:
                tracker=json.loads((STATE/'dream_tracker.json').read_text())
                session_id=tracker.get('session_id')
            except Exception:
                pass
            result_path=STATE/'physical_suspend_result.json'
            result_path.write_text(json.dumps({
                'session_id':session_id,
                'timestamp':time.time(),
                **outcome
            },separators=(',',':')))
            if outcome['completed']:
                write_status('resumed', lifecycle_phase=phase, **outcome)
                tracker_event('physical_suspend_completed',session_id,**outcome)
            else:
                write_status('suspend_failed', lifecycle_phase=phase, **outcome)
                tracker_event('physical_suspend_failed',session_id,**outcome)

            time.sleep(1)
        elif not previous and current:
            write_status('opening')
            write_request('wake','physical lid opened')
            tracker_event('wake_signal','physical_lid')
            write_status('awake')
        previous=current
        time.sleep(POLL)

if __name__=='__main__':
    main()
