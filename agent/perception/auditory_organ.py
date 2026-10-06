from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
FOCUS = STATE / "hearing_focus.json"
OUTPUT = STATE / "auditory_perception.json"


DEFAULT = {
    "mode": "external",
    "source": "environment",
    "frequency": 1000.0,
    "bandwidth": 0.55,
    "temporal_window": 0.35,
    "gain": 1.0,
    "reason": "default_auditory_attention",
    "timestamp": 0.0,
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))


def read_focus():
    try:
        data = json.loads(FOCUS.read_text())
    except Exception:
        data = {}
    out = dict(DEFAULT)
    out.update(data)
    out["frequency"] = _clamp(out.get("frequency", 1000), 60, 16000)
    out["bandwidth"] = _clamp(out.get("bandwidth", .55), .08, 1.0)
    out["temporal_window"] = _clamp(out.get("temporal_window", .35), .05, 1.0)
    out["gain"] = _clamp(out.get("gain", 1.0), .2, 2.5)
    return out


def set_focus(source=None, frequency=None, bandwidth=None,
              temporal_window=None, gain=None, mode=None, reason="attention"):
    d = read_focus()
    if source is not None:
        d["source"] = str(source)
    if frequency is not None:
        d["frequency"] = _clamp(frequency, 60, 16000)
    if bandwidth is not None:
        d["bandwidth"] = _clamp(bandwidth, .08, 1.0)
    if temporal_window is not None:
        d["temporal_window"] = _clamp(temporal_window, .05, 1.0)
    if gain is not None:
        d["gain"] = _clamp(gain, .2, 2.5)
    if mode is not None:
        d["mode"] = str(mode)
    d["reason"] = reason
    d["timestamp"] = time.time()
    STATE.mkdir(parents=True, exist_ok=True)
    FOCUS.write_text(json.dumps(d, separators=(",", ":")))
    return d


def _band_edges(rate, count=12):
    low, high = 60.0, min(16000.0, rate / 2.0)
    return np.geomspace(low, high, count + 1)


def process(samples, rate, channels, focus=None):
    """Auditory equivalent of the visual Sight Organ.

    Raw microphone signal becomes a sparse perceptual representation:
    coarse all-band awareness + a high-resolution attended acoustic band.
    """
    focus = focus or read_focus()
    data = np.asarray(samples, dtype=np.float32)
    if data.size == 0:
        return {"available": False}

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    # Keep the temporal signal short and stable for the old laptop.
    data = data[-min(len(data), int(rate * 1.0)):]
    rms = float(np.sqrt(np.mean(data * data)) / 32768.0)
    peak = float(np.max(np.abs(data)) / 32768.0)

    window = np.hanning(len(data))
    spectrum = np.abs(np.fft.rfft(data * window))
    freqs = np.fft.rfftfreq(len(data), 1.0 / rate)

    edges = _band_edges(rate)
    bands = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (freqs >= lo) & (freqs < hi)
        energy = float(np.mean(spectrum[mask])) if np.any(mask) else 0.0
        bands.append({"low": round(float(lo)), "high": round(float(hi)), "energy": round(energy, 3)})

    target = float(focus["frequency"])
    width = max(0.08, float(focus["bandwidth"]))
    # Log-frequency distance makes the focus behave more like pitch attention.
    distances = np.abs(np.log2(np.maximum(freqs, 1.0) / target))
    sigma = width * 1.8
    attention_mask = np.exp(-(distances ** 2) / (2.0 * sigma ** 2))

    attended_energy = float(np.mean(spectrum * attention_mask))
    total_energy = float(np.mean(spectrum) + 1e-9)
    focus_ratio = attended_energy / total_energy

    # The unattended sound is compressed into broad band energies.
    # The attended band keeps richer frequency information.
    attended_bins = [
        (round(float(f), 1), round(float(v), 3))
        for f, v, a in zip(freqs[::max(1, len(freqs)//96)],
                            spectrum[::max(1, len(spectrum)//96)],
                            attention_mask[::max(1, len(attention_mask)//96)])
        if a > 0.25
    ][:96]

    temporal = np.abs(data[1:] - data[:-1])
    transient = float(np.mean(temporal) / 32768.0) if len(temporal) else 0.0

    mode = str(focus.get("mode", "external"))
    external_gain = float(focus.get("gain", 1.0))
    if mode in {"internal", "inward"}:
        external_gain *= 0.35

    result = {
        "available": True,
        "timestamp": time.time(),
        "rate": int(rate),
        "channels": int(channels),
        "rms": round(rms, 6),
        "peak": round(peak, 6),
        "transient": round(transient, 6),
        "coarse_bands": bands,
        "attended_frequency": round(target, 1),
        "attended_bandwidth": round(width, 3),
        "attended_spectrum": attended_bins,
        "focus_ratio": round(min(1.0, focus_ratio), 4),
        "external_gain": round(external_gain, 3),
        "temporal_window": float(focus.get("temporal_window", .35)),
        "peripheral_compression": True,
        "focal_acoustic_detail": True,
        "source": focus.get("source", "environment"),
    }
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, separators=(",", ":")))
    return result
