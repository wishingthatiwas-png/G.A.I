from __future__ import annotations

import json
import math
import os
import struct
import subprocess
import time
import wave
from pathlib import Path

ROOT = Path('/mnt/gai')
STATE = ROOT / 'state'
REQUEST = STATE / 'speaker_request.json'
BODY = STATE / 'body_output.json'
STATUS = STATE / 'speaker_organ.json'
SPEECH_RESULT = STATE / 'speech_output.json'
TONES = {
    'curiosity': 660.0, 'happiness': 784.0, 'contentment': 523.0,
    'fear': 220.0, 'stress': 180.0, 'fatigue': 260.0,
    'boredom': 330.0, 'neutral': 440.0,
}


def _write_status(**extra):
    payload = {'persistent': True, 'timestamp': time.time()}
    try:
        current = json.loads(STATUS.read_text())
        if isinstance(current, dict):
            payload.update(current)
    except Exception:
        pass
    payload.update(extra)
    STATUS.write_text(json.dumps(payload, separators=(',', ':')))
    return payload


def _play_tone(req):
    emotion = str(req.get('emotion', 'neutral'))
    frequency = float(req.get('frequency', TONES.get(emotion, 440.0)))
    duration = max(0.04, min(1.5, float(req.get('duration', 0.12))))
    amplitude = max(0.01, min(0.12, float(req.get('amplitude', 0.08))))
    n = int(44100 * duration)
    frames = bytearray()
    for i in range(n):
        t = i / 44100.0
        env = min(1.0, t / 0.018, (duration - t) / 0.035)
        x = int(32767 * amplitude * max(0.0, env) * math.sin(2 * math.pi * frequency * t))
        frames += struct.pack('<hh', x, x)
    out = STATE / 'audio_output' / 'speaker_organ.wav'
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(44100); wf.writeframes(frames)
    env = dict(os.environ)
    env.setdefault('XDG_RUNTIME_DIR', '/run/user/1000')
    proc = subprocess.run(['pw-play', str(out)], env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=max(2.0, duration + 2))
    return proc.returncode == 0, {'emotion': emotion, 'frequency': frequency, 'duration': duration}


def _start_speech(text):
    text = ' '.join(str(text or '').split())[:240]
    if not text:
        return None, 'empty_text'
    # speech-dispatcher is the text-to-speech boundary for V1; the motor layer
    # submits text, but this organ owns actual audio output.
    proc = subprocess.Popen(
        ['spd-say', '--wait', text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc, None


def play(req):
    mode = str(req.get('mode', 'affective_tone'))
    text = ' '.join(str(req.get('text', '') or '').split())[:240]
    now = time.time()
    try:
        if mode == 'speech' and text:
            proc, err = _start_speech(text)
            if err:
                raise RuntimeError(err)
            correlation_id = req.get('correlation_id')
            _write_status(last=now, accepted=True, playing=True, audio_active=True,
                          mode='speech', text=text, speech_pid=proc.pid,
                          speech_status='started', correlation_id=correlation_id, error='')
            body = json.loads(BODY.read_text()) if BODY.exists() else {}
            body.update({'timestamp': now, 'audio_active': True, 'mode': 'speech',
                         'text': text, 'emotion': req.get('emotion', 'neutral'),
                         'speech_pid': proc.pid, 'speech_status': 'started',
                         'correlation_id': correlation_id})
            BODY.write_text(json.dumps(body, separators=(',', ':')))
            return
        ok, meta = _play_tone(req)
        _write_status(last=now, accepted=True, playing=ok, audio_active=ok,
                      mode='affective_tone', **meta, text=text, error='' if ok else 'pw_play_failed')
        body = json.loads(BODY.read_text()) if BODY.exists() else {}
        body.update({'timestamp': now, 'audio_active': ok, 'mode': 'affective_tone',
                     'emotion': meta['emotion'], 'frequency': meta['frequency'],
                     'duration': meta['duration'], 'rms': 0.08 / math.sqrt(2) if ok else 0,
                     'peak': 0.08 if ok else 0, 'text': text})
        BODY.write_text(json.dumps(body, separators=(',', ':')))
    except Exception as exc:
        _write_status(last=now, accepted=True, playing=False, audio_active=False,
                      mode=mode, text=text, speech_status='failed',
                      correlation_id=req.get('correlation_id'), error=str(exc))
        try:
            body = json.loads(BODY.read_text()) if BODY.exists() else {}
            body.update({'timestamp': now, 'audio_active': False, 'mode': mode,
                         'text': text, 'speech_status': 'failed',
                         'correlation_id': req.get('correlation_id'), 'error': str(exc)})
            BODY.write_text(json.dumps(body, separators=(',', ':')))
            SPEECH_RESULT.write_text(json.dumps({
                'status': 'failed', 'mode': mode, 'text': text,
                'correlation_id': req.get('correlation_id'), 'timestamp': now,
                'success': False, 'error': str(exc)
            }, separators=(',', ':')))
        except Exception:
            pass


def _pid_running(pid):
    try:
        state = Path(f'/proc/{int(pid)}/stat').read_text().split()[2]
        return state != 'Z'
    except Exception:
        return False


def main():
    STATUS.write_text(json.dumps({'persistent': True, 'started': time.time(),
                                  'playing': False, 'audio_active': False,
                                  'mode': 'affective_tone', 'error': ''}))
    last = 0.0
    speech_pid = None
    while True:
        try:
            if speech_pid and not _pid_running(speech_pid):
                _write_status(playing=False, audio_active=False, speech_status='completed',
                              speech_pid=None, completed=time.time())
                completed = time.time()
                try:
                    body = json.loads(BODY.read_text()) if BODY.exists() else {}
                    body.update({'audio_active': False, 'speech_status': 'completed',
                                 'speech_pid': None, 'completed': completed})
                    BODY.write_text(json.dumps(body, separators=(',', ':')))
                    SPEECH_RESULT.write_text(json.dumps({
                        'status': 'completed', 'mode': 'speech', 'text': body.get('text',''),
                        'correlation_id': body.get('correlation_id'), 'timestamp': completed,
                        'success': True, 'error': ''
                    }, separators=(',', ':')))
                except Exception:
                    pass
                speech_pid = None
            req = json.loads(REQUEST.read_text())
            ts = float(req.get('timestamp', 0))
            if ts > last:
                last = ts
                mode = str(req.get('mode', 'affective_tone'))
                if mode == 'speech' and speech_pid:
                    try:
                        os.kill(speech_pid, 15)
                    except Exception:
                        pass
                    speech_pid = None
                play(req)
                if mode == 'speech':
                    try:
                        speech_pid = int(json.loads(STATUS.read_text()).get('speech_pid') or 0) or None
                    except Exception:
                        speech_pid = None
        except Exception:
            pass
        time.sleep(0.08)


if __name__ == '__main__':
    main()
