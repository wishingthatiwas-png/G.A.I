import json
import logging
import os
import time
from pathlib import Path
from .state import InternalState
from .drives import DriveState
from .world import WorldState
from .memory import Memory

ROOT = Path('/mnt/gai')
CONFIG = ROOT / 'config/agent.json'

class Kernel:
    def __init__(self):
        cfg = json.loads(CONFIG.read_text())
        self.cfg = cfg
        self.state = InternalState()
        self.drives = DriveState()
        self.world = WorldState()
        self.memory = Memory(cfg['memory_db'])
        Path(cfg['log_file']).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=cfg['log_file'], level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        self.log = logging.getLogger('gai')

    def snapshot(self):
        return {'state': self.state.snapshot(), 'drives': vars(self.drives), 'world': vars(self.world)}

    def tick(self):
        self.state.update_time()
        self.state.mode = self.drives.strongest()
        snap = self.snapshot()
        (ROOT / 'state/runtime.json').write_text(json.dumps(snap, indent=2))
        return snap

    def run(self):
        self.log.info('G.A.I. kernel starting')
        while True:
            self.tick()
            time.sleep(self.cfg.get('tick_seconds', 2))

if __name__ == '__main__':
    Kernel().run()
