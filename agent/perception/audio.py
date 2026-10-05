from __future__ import annotations
import numpy as np
import sounddevice as sd

def devices():
    return sd.query_devices()

def default_input():
    return sd.query_devices(kind='input')

def sample(duration=0.15, samplerate=None):
    if samplerate is None:
        samplerate = int(sd.query_devices(kind='input')['default_samplerate'])
    data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32', blocking=True)
    rms = float(np.sqrt(np.mean(np.square(data))))
    peak = float(np.max(np.abs(data)))
    return {'rms': rms, 'peak': peak, 'duration': duration, 'samplerate': samplerate}
