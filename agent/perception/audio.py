from __future__ import annotations
import sounddevice as sd


def devices():
    return sd.query_devices()


def default_input():
    return sd.query_devices(kind='input')
