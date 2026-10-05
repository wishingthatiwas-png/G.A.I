import psutil

def level_and_charging():
    b=psutil.sensors_battery()
    if b is None: return 1.0, False
    return float(b.percent)/100.0, bool(b.power_plugged)
