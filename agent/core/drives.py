from dataclasses import dataclass


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

@dataclass
class DriveState:
    explore: float = 0.5
    rest: float = 0.0
    interact: float = 0.5
    maintain: float = 0.2

    def update(self, state, perception):
        avail = perception.get('system', {}).get('memory_available') or 0
        total = perception.get('system', {}).get('memory_total') or 1
        mem_pressure = 1.0 - avail / total
        load = perception.get('system', {}).get('load_1m', 0.0)
        gpu = perception.get('hardware', {}).get('nvidia') or ''
        screen_present = bool((perception.get('senses', {}).get('visual_stream') or {}).get('available'))

        sleep_need = float(getattr(state, "sleep_need", 0.0))
        self.rest = clamp(
            0.12 * state.fatigue
            + 0.28 * sleep_need
            + 0.35 * min(1.0, load / max(1, state.cpu_count if hasattr(state, 'cpu_count') else 4))
        )
        self.maintain = clamp(0.15 + 0.65 * mem_pressure + (0.1 if not screen_present else 0))
        self.interact = clamp(0.25 + 0.25 * state.curiosity + 0.15 * state.satisfaction)
        self.explore = clamp(0.65 + 0.25 * state.curiosity - 0.35 * self.rest - 0.2 * self.maintain)

    def strongest(self):
        return max(vars(self), key=vars(self).get)
