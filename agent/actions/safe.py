from __future__ import annotations
from pathlib import Path
import json, time

ROOT = Path('/mnt/gai')

class SafeActions:
    """Non-destructive actions available to the autonomous loop."""
    def log(self, action, **details):
        p = ROOT / 'data/actions.jsonl'
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a') as f:
            f.write(json.dumps({'ts': time.time(), 'action': action, 'details': details}) + '\n')

    def save_observation(self, observation):
        p = ROOT / 'data/observations/latest.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(observation, indent=2, default=str))
        self.log('save_observation')
