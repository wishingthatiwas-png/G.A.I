from dataclasses import dataclass

@dataclass
class DriveState:
    explore: float = 0.5
    rest: float = 0.0
    interact: float = 0.5
    maintain: float = 0.2

    def strongest(self):
        return max(vars(self), key=vars(self).get)
