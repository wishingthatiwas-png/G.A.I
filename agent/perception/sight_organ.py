from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
PERCEPT = STATE / "perceptual_vision.png"
SOURCES = STATE / "sight_sources.json"
ADAPT = STATE / "sight_adaptation.json"


def _run(cmd, timeout=2):
    try:
        env = dict(os.environ)
        env.setdefault("DISPLAY", ":0")
        env.setdefault("XAUTHORITY", "/home/null/.Xauthority")
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL,
                                       timeout=timeout, env=env)
    except Exception:
        return ""


def discover_sources():
    """Inventory the visual organs available to the organism.

    The desktop screenshot is treated as one visual surface, while xrandr,
    X11 windows and V4L2 devices describe the sources contained around it.
    """
    monitors = []
    raw = _run(["xrandr", "--query"])
    for line in raw.splitlines():
        m = re.search(r"^([^ ]+) connected(?: primary)? (\d+x\d+)(?:\+(\-?\d+))?\+(\-?\d+)?", line)
        if m:
            monitors.append({
                "name": m.group(1),
                "geometry": m.group(2),
                "connected": True,
            })

    windows = []
    raww = _run(["wmctrl", "-lG"])
    for line in raww.splitlines():
        parts = line.split(None, 7)
        if len(parts) >= 7:
            try:
                windows.append({
                    "id": parts[0],
                    "x": int(parts[2]),
                    "y": int(parts[3]),
                    "width": int(parts[4]),
                    "height": int(parts[5]),
                    "title": parts[7] if len(parts) > 7 else "",
                })
            except Exception:
                pass

    cameras = []
    for dev in sorted(STATE.parent.glob("dummy-do-not-match")):
        pass
    for dev in (Path("/dev/video0"), Path("/dev/video1"), Path("/dev/video2"),
                Path("/dev/video3"), Path("/dev/video4"), Path("/dev/video5")):
        if dev.exists():
            cameras.append({"device": str(dev), "available": True})

    result = {
        "timestamp": time.time(),
        "monitors": monitors,
        "windows": windows,
        "cameras": cameras,
        "monitor_count": len(monitors),
        "window_count": len(windows),
        "camera_count": len(cameras),
        "visual_source_count": len(monitors) + len(cameras),
    }
    STATE.mkdir(parents=True, exist_ok=True)
    SOURCES.write_text(json.dumps(result, separators=(",", ":")))
    return result


def _focus_box(size, focus):
    w, h = size
    x = max(0.0, min(1.0, float(focus.get("x", 0.5))))
    y = max(0.0, min(1.0, float(focus.get("y", 0.78))))
    r = max(0.08, min(0.35, float(focus.get("radius", 0.18))))
    fw = max(24, int(w * r * 2))
    fh = max(24, int(h * r * 2))
    left = max(0, min(w - fw, int(x * w - fw / 2)))
    top = max(0, min(h - fh, int(y * h - fh / 2)))
    return (left, top, left + fw, top + fh), (x, y, r)


def _local_exposure(im, box):
    """Slow retinal light adaptation: bright scenes close the pupil, dark scenes open it."""
    crop = im.crop(box)
    stat = ImageStat.Stat(crop)
    brightness = sum(stat.mean) / 3.0
    now = time.time()
    target = max(0.55, min(1.55, 118.0 / max(18.0, brightness)))
    try:
        state = json.loads(ADAPT.read_text())
    except Exception:
        state = {"gain": 1.0, "timestamp": now}
    previous = max(0.55, min(1.55, float(state.get("gain", 1.0))))
    dt = max(0.0, min(2.0, now - float(state.get("timestamp", now))))
    # Eyes adapt quickly to sudden brightness, but recover from darkness more gently.
    tau = 0.55 if target < previous else 1.35
    alpha = 1.0 - pow(2.718281828, -dt / tau) if dt > 0 else 0.0
    gain = previous + (target - previous) * alpha
    ADAPT.parent.mkdir(parents=True, exist_ok=True)
    ADAPT.write_text(json.dumps({"gain": gain, "timestamp": now, "scene_brightness": brightness, "target_gain": target}, separators=(",", ":")))
    out = ImageEnhance.Brightness(im).enhance(gain)
    contrast = max(0.82, min(1.22, 1.0 + (128.0 - brightness) / 420.0))
    out = ImageEnhance.Contrast(out).enhance(contrast)
    pupil = max(0.12, min(1.0, 0.58 + 0.42 * (gain - 0.55) / 1.0))
    return out, round(brightness, 1), round(gain, 3), round(pupil, 3)


def _peripheral_compress(im, box, radius):
    """Keep a foveal island detailed and progressively compress the periphery."""
    w, h = im.size

    # Very cheap peripheral representation: downsample aggressively then restore.
    small_w = max(32, w // 10)
    small_h = max(32, h // 10)
    peripheral = im.resize((small_w, small_h), Image.Resampling.BILINEAR)
    peripheral = peripheral.resize((w, h), Image.Resampling.BILINEAR)
    peripheral = peripheral.filter(ImageFilter.GaussianBlur(max(2.0, min(8.0, radius * 18.0))))

    # A second, slightly less compressed band prevents the entire world from
    # becoming a featureless blur. It gives coarse motion/colour awareness.
    band = im.resize((max(48, w // 5), max(48, h // 5)), Image.Resampling.BILINEAR)
    band = band.resize((w, h), Image.Resampling.BILINEAR)
    band = band.filter(ImageFilter.GaussianBlur(1.4))

    # Smooth radial mask centred on the current gaze point.
    cx = (box[0] + box[2]) / 2.0
    cy = (box[1] + box[3]) / 2.0
    rx = max(18.0, (box[2] - box[0]) / 2.0)
    ry = max(18.0, (box[3] - box[1]) / 2.0)

    # Build the radial attention mask at low resolution and upscale it.
    # This keeps the visual organ cheap enough for an old laptop.
    mw, mh = max(32, w // 8), max(32, h // 8)
    mask_small = Image.new("L", (mw, mh), 0)
    px = mask_small.load()
    sx, sy = mw / max(1, w), mh / max(1, h)
    for yy in range(mh):
        dy = (yy / sy - cy) / ry
        for xx in range(mw):
            dx = (xx / sx - cx) / rx
            d = (dx * dx + dy * dy) ** 0.5
            value = 255 if d <= 1.0 else (0 if d >= 2.2 else int(255 * (2.2 - d) / 1.2))
            px[xx, yy] = value
    mask = mask_small.resize((w, h), Image.Resampling.BICUBIC)

    # Blend: sharp fovea, intermediate parafovea, compressed periphery.
    out = Image.composite(im, band, mask)
    # A broad mask for the truly peripheral layer.
    broad = ImageOps.invert(mask).filter(ImageFilter.GaussianBlur(18))
    out = Image.composite(out, peripheral, broad)

    # Re-apply the exact foveal patch at full fidelity.
    fovea = im.crop(box)
    out.paste(fovea, box)
    return out


def _colour_adapt(im, focus_box):
    """Crude automatic white-balance / saturation adaptation."""
    crop = im.crop(focus_box)
    mean = ImageStat.Stat(crop).mean
    avg = max(1.0, sum(mean) / 3.0)
    # Neutralise strong casts very gently rather than destroying scene colour.
    gains = [max(0.88, min(1.12, avg / max(1.0, c))) for c in mean]
    channels = im.split()
    adjusted = []
    for channel, gain in zip(channels, gains):
        adjusted.append(ImageEnhance.Brightness(channel).enhance(gain))
    out = Image.merge("RGB", adjusted)
    return ImageEnhance.Color(out).enhance(1.04)


def process(image_path, focus):
    """Turn a raw stitched field into the Sight Organ's perceptual output."""
    im = Image.open(image_path).convert("RGB")
    box, (x, y, radius) = _focus_box(im.size, focus)

    adapted, scene_brightness, exposure, pupil = _local_exposure(im, box)
    adapted = _colour_adapt(adapted, box)

    mode = str(focus.get("mode", "in"))
    eyes_open = float(focus.get("eyes_open", 0.72))
    if eyes_open < 0.08:
        # Closed eyes = no external visual signal.
        percept = Image.new("RGB", im.size, (0, 0, 0))
    else:
        percept = _peripheral_compress(adapted, box, radius)

        # Looking inward lowers external visual gain. The image remains present
        # for body diagnostics, but cognition receives a much weaker external field.
        if mode == "in":
            percept = ImageEnhance.Brightness(percept).enhance(
                max(0.45, min(0.9, 0.45 + eyes_open * 0.55))
            )

    STATE.mkdir(parents=True, exist_ok=True)
    percept.save(PERCEPT, quality=88)

    meta = {
        "timestamp": time.time(),
        "source_image": str(image_path),
        "output_image": str(PERCEPT),
        "mode": mode,
        "focus": {"x": x, "y": y, "radius": radius},
        "focus_box": box,
        "scene_brightness": scene_brightness,
        "exposure_gain": exposure,
        "pupil_open": pupil,
        "light_adaptation": True,
        "peripheral_compression": True,
        "foveal_detail": True,
        "colour_adaptation": True,
        "eyes_open": eyes_open,
    }
    return meta
