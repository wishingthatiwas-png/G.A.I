from __future__ import annotations

import json
import math
import os
import struct
import subprocess
import threading
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path("/mnt/gai")
BODY_OUTPUT = ROOT / "state/body_output.json"


class AudioOrgan:
    """Persistent speaker request interface plus optional affect tone fallback."""
    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self._lock = threading.Lock()
        self._busy = False

    def _tone(self, frequency: float, duration: float, amplitude: float = 0.08):
        try:
            n = max(1, int(self.samplerate * duration))
            t = np.arange(n, dtype=np.float32) / self.samplerate
            attack = np.minimum(1.0, t / 0.018)
            release = np.minimum(1.0, (duration - t) / 0.035)
            envelope = np.clip(np.minimum(attack, release), 0.0, 1.0)
            wave_data = []
            for i in range(n):
                x = int(32767 * amplitude * float(envelope[i]) * math.sin(2 * math.pi * frequency * float(t[i])))
                wave_data.append(struct.pack("<hh", x, x))
            out = ROOT / "state/audio_output/affect.wav"
            out.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(out), "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(self.samplerate)
                wf.writeframes(b"".join(wave_data))
            env = dict(os.environ)
            env.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
            played = subprocess.run(
                ["pw-play", str(out)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=max(2.0, duration + 2),
            ).returncode == 0
            return float(amplitude / math.sqrt(2)), float(amplitude) if played else (0.0, 0.0)
        except Exception:
            return 0.0, 0.0

    def emit(self, emotion: str = "neutral", action: str = "none") -> dict:
        tones = {
            "curiosity": (660.0, 0.10),
            "happiness": (784.0, 0.12),
            "contentment": (523.0, 0.16),
            "fear": (220.0, 0.10),
            "stress": (180.0, 0.08),
            "fatigue": (260.0, 0.16),
            "boredom": (330.0, 0.10),
            "neutral": (440.0, 0.08),
        }
        key = emotion if emotion in tones else "neutral"
        frequency, duration = tones[key]
        if action in {"rest", "maintain"}:
            duration *= 1.15
        with self._lock:
            if self._busy:
                return {"audio_active": False, "rms": 0.0, "peak": 0.0, "emotion": key}
            self._busy = True
        try:
            rms, peak = self._tone(frequency, duration)
            return {
                "audio_active": bool(peak > 0),
                "rms": rms,
                "peak": peak,
                "emotion": key,
                "frequency": frequency,
                "duration": duration,
                "timestamp": time.time(),
            }
        finally:
            self._busy = False


_AUDIO = AudioOrgan()


def _speech_waveform(text: str, points: int = 64) -> list[float]:
    """Compact mouth-audiograph envelope derived from the spoken text."""
    text = " ".join(str(text or "").split())
    if not text:
        return [0.0] * points
    vowels = set("aeiouy")
    values = []
    for i in range(points):
        ch = text[int(i * len(text) / points) % len(text)].lower()
        base = 0.72 if ch in vowels else 0.42
        if ch in " ,.!?":
            base = 0.08
        if ch in "mnbpl":
            base = 0.56
        values.append(round(base, 3))
    return values


def emit_affect(emotion: str, action: str, text: str = "", correlation_id: str | None = None) -> dict:
    request = ROOT / "state/speaker_request.json"
    request.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    clean_text = " ".join(str(text or "").split())[:240]
    result = {
        "audio_active": False,
        "rms": 0.0,
        "peak": 0.0,
        "emotion": emotion,
        "action": action,
        "timestamp": now,
        "organ": "speaker",
        "persistent": True,
        "mode": "speech" if clean_text else "affective_tone",
        "text": clean_text,
        "correlation_id": correlation_id,
        "waveform": _speech_waveform(clean_text),
    }
    request.write_text(json.dumps(result, separators=(",", ":")))
    try:
        payload = json.loads(BODY_OUTPUT.read_text()) if BODY_OUTPUT.exists() else {}
        payload.update(result)
        BODY_OUTPUT.write_text(json.dumps(payload, separators=(",", ":")))
    except Exception:
        pass
    return result
