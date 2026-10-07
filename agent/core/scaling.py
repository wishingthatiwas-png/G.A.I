"""Shared G.A.I. compute scaling.

One hardware-normalized compute scale drives both CNS tick cadence and the
continuous metabolic cadence. Simulation speed is a separate time-dilation
multiplier. This lets the same organism scale from an old laptop to a faster
machine without changing its behavioural model.
"""
from __future__ import annotations
import math
import os

BASE_TICK_FPS = 20.0
BASE_METABOLIC_HZ = 2.0
SPEED_LEVELS = (0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0)


def compute_scale(config: dict) -> float:
    try:
        value = float(config.get("compute_scale", config.get("metabolic_capacity", 1.0)))
    except (TypeError, ValueError):
        value = 1.0
    return max(0.1, value)


def simulation_speed(path_value: float = 1.0) -> float:
    return max(0.1, min(10.0, float(path_value)))


def effective_tick_fps(config: dict, speed: float = 1.0) -> float:
    return BASE_TICK_FPS * compute_scale(config) * simulation_speed(speed)


def effective_metabolic_hz(config: dict, speed: float = 1.0) -> float:
    return BASE_METABOLIC_HZ * compute_scale(config) * simulation_speed(speed)


def worker_ceiling() -> int:
    return max(1, (os.cpu_count() or 2) - 1)


def neural_population_target(config: dict) -> int:
    """Bounded neural-agent scaling; keep V1 substrate data-only and non-authoritative."""
    try:
        requested = int(config.get("neural_population_target", 256))
    except (TypeError, ValueError):
        requested = 256
    scaled = int(round(requested * math.sqrt(compute_scale(config))))
    return max(64, min(512, scaled))


def worker_count(config: dict) -> int:
    # Parallelism grows sub-linearly; cadence is the primary scaling mechanism.
    return max(1, min(int(math.ceil(math.sqrt(compute_scale(config)))), worker_ceiling()))


def character_budget(scale: float | int) -> int:
    return max(50, int(50 * max(1.0, float(scale))))
