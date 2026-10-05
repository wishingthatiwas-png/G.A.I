import json
import logging
import os
import time
from pathlib import Path
from .state import InternalState
from .drives import DriveState
from .world import WorldState
from .memory import Memory
from memory.engram import AssociativeMemory
from actions.safe import SafeActions
from perception.screen import snapshot as screen_snapshot
from perception.senses import Senses
from perception.system import snapshot as system_snapshot
from perception.hardware import snapshot as hardware_snapshot

ROOT = Path('/mnt/gai')
CONFIG = ROOT / 'config/agent.json'

class Kernel:
    def __init__(self):
        cfg = json.loads(CONFIG.read_text())
        self.cfg = cfg
        self.state = InternalState()
        self.drives = DriveState()
        self.world = WorldState()
        self.last_system = {}
        self.last_hardware = {}
        self.last_action = {'type': 'none'}
        self.actions = SafeActions()
        self.last_screen = {}
        self.senses = Senses()
        self.last_senses = {}
        self.memory = Memory(cfg['memory_db'])
        self.associative = AssociativeMemory()
        Path(cfg['log_file']).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=cfg['log_file'], level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        self.log = logging.getLogger('gai')

    def snapshot(self):
        return {'state': self.state.snapshot(), 'drives': vars(self.drives), 'world': vars(self.world), 'perception': {'system': self.last_system, 'hardware': self.last_hardware, 'screen': self.last_screen, 'senses': self.last_senses}, 'action': self.last_action}

    def tick(self):
        self.state.update_time()
        self.last_system = system_snapshot()
        self.last_hardware = hardware_snapshot()
        self.last_screen = screen_snapshot()
        self.last_senses = self.senses.observe()
        perception = {'system': self.last_system, 'hardware': self.last_hardware, 'screen': self.last_screen, 'senses': self.last_senses}
        self.world.observe(perception)
        self.drives.update(self.state, perception)
        self.state.mode = self.drives.strongest()
        self.last_action = self.decide()
        self.actions.save_observation(perception)
        stimuli = ['system', 'camera_present' if self.last_senses.get('camera') else 'camera_absent', self.state.mode]
        vision = self.last_senses.get('vision') or {}
        stimuli.extend(vision.get('concepts', [])[:24])
        audio = self.last_senses.get('audio') or {}
        if isinstance(audio, dict) and audio.get('rms', 0) > 0.03:
            stimuli.append('sound_present')
        emotions = {'curiosity': self.state.curiosity, 'stress': self.state.stress, 'satisfaction': self.state.satisfaction, 'fatigue': self.state.fatigue}
        self.associative.fire(stimuli, emotions=emotions, context={'action': self.last_action, 'observation': self.world.observation_count}, reward=self.state.satisfaction-self.state.stress)
        self.memory.remember('tick', {'mode': self.state.mode, 'drives': vars(self.drives), 'action': self.last_action, 'stimuli': stimuli})
        snap = self.snapshot()
        (ROOT / 'state/runtime.json').write_text(json.dumps(snap, indent=2))
        return snap

    def decide(self):
        if self.state.mode == 'rest':
            return {'type': 'rest', 'reason': 'fatigue/load'}
        if self.state.mode == 'maintain':
            return {'type': 'maintain', 'reason': 'system pressure'}
        if self.state.mode == 'interact':
            return {'type': 'interact', 'reason': 'interaction drive'}
        return {'type': 'explore', 'reason': 'curiosity/low pressure'}

    def run(self):
        self.log.info('G.A.I. kernel starting')
        while True:
            self.tick()
            time.sleep(self.cfg.get('tick_seconds', 2))

if __name__ == '__main__':
    Kernel().run()
