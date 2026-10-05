



import json
import logging
import time
from pathlib import Path

from .state import InternalState
from .drives import DriveState
from .world import WorldState
from .memory import Memory
from .signals import SignalBus
from .control import ControlCentre
from .learning import OutcomeLearner
from .prediction import PredictiveModel
from .lifecycle import Lifecycle
from .dream import DreamEngine
from .evolution import EvolutionEngine
from .power import level_and_charging
from .working_memory import WorkingMemoryCell
from .cells import (
    PerceptionCell, DriveCell, PredictionCell, ControlCell,
    ActionCell, MemoryCell, LifecycleCell, NervousSupervisor,
)
from memory.engram import AssociativeMemory
from memory.semantic import SemanticNetwork
from actions.safe import SafeActions
from perception.screen import snapshot as screen_snapshot
from perception.senses import Senses
from perception.system import snapshot as system_snapshot
from perception.hardware import snapshot as hardware_snapshot

ROOT = Path("/mnt/gai")
CONFIG = ROOT / "config/agent.json"


class Kernel:
    def __init__(self):
        cfg = json.loads(CONFIG.read_text())
        self.cfg = cfg
        self.state = InternalState()
        self.drives = DriveState()
        self.world = WorldState()
        self.last_system = {}
        self.last_hardware = {}
        self.last_action = {"type": "none"}
        self.last_screen = {}
        self.last_senses = {}
        self.latest_prediction_error = 0.0
        self.latest_outcome_error = 0.0
        self.current_correlation = None

        self.actions = SafeActions()
        self.senses = Senses()
        self.memory = Memory(cfg["memory_db"])
        self.associative = AssociativeMemory()
        self.semantic = SemanticNetwork()
        self.bus = SignalBus()
        self.learner = OutcomeLearner()
        self.predictor = PredictiveModel()
        self.nervous = self.bus.nervous

        self.control = ControlCentre(self.bus, self.learner, self.predictor)
        self.lifecycle = Lifecycle()
        self.evolution = EvolutionEngine()
        self.dream = DreamEngine(self.evolution)
        self.dream_last_report = None

        self._register_cells()

        Path(cfg["log_file"]).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=cfg["log_file"],
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        self.log = logging.getLogger("gai")
        self.sync_phenotype()

    def _register_cells(self):
        self.nervous.register_component(
            "kernel", kind="core", version="0.2.0", sleep_capable=False, critical=True
        )
        self.perception_cell = PerceptionCell(self).start()
        self.drive_cell = DriveCell(self).start()
        self.prediction_cell = PredictionCell(self).start()
        self.control_cell = ControlCell(self).start()
        self.action_cell = ActionCell(self).start()
        self.memory_cell = MemoryCell(self).start()
        self.working_memory = WorkingMemoryCell(self.nervous).start()

        active = [
            self.perception_cell,
            self.drive_cell,
            self.prediction_cell,
            self.control_cell,
            self.action_cell,
        ]
        self.lifecycle_cell = LifecycleCell(self, active).start()
        self.supervisor = NervousSupervisor(self).start()
        self.cells = [
            self.perception_cell, self.drive_cell, self.prediction_cell,
            self.control_cell, self.action_cell, self.memory_cell,
            self.working_memory, self.lifecycle_cell, self.supervisor,
        ]

    def sync_phenotype(self):
        genes = self.evolution.phenotype()
        self.learner.learning_rate = genes["prediction_lr"]
        self.predictor.learning_rate = genes["prediction_lr"]
        self.associative.association_gain = genes["association_gain"]
        self.control.params = genes

    def drive_values(self):
        return {
            "curiosity": self.state.curiosity,
            "satisfaction": self.state.satisfaction,
            "safety": self.state.stress,
            "energy": self.state.fatigue,
            "social": 0.0,
        }

    def current_context(self):
        vision = self.last_senses.get("vision") or {}
        concepts = vision.get("concepts", [])
        context = ["camera" if self.last_senses.get("camera") else "no_camera"]
        context.extend(concepts[:16])
        audio = self.last_senses.get("audio") or {}
        if isinstance(audio, dict) and float(audio.get("rms", 0.0)) > .03:
            context.append("sound")
        context.append(self.state.mode)
        return context

    def perception_novelty(self):
        concepts = (self.last_senses.get("vision") or {}).get("concepts", [])
        return 1.0 if any(c not in self.associative.neurons for c in concepts) else 0.0

    def system_snapshot(self):
        return system_snapshot()

    def hardware_snapshot(self):
        return hardware_snapshot()

    def screen_snapshot(self):
        return screen_snapshot()

    def emit(self, kind, payload=None, **kwargs):
        return self.nervous.publish(kind, payload, source="kernel", **kwargs)

    def snapshot(self):
        return {
            "state": self.state.snapshot(),
            "drives": vars(self.drives),
            "world": vars(self.world),
            "signals": self.bus.snapshot(),
            "learning": self.bus.learning_snapshot(),
            "nervous": self.bus.nervous_snapshot(),
            "working_memory": self.working_memory.snapshot(),
            "outcome_model": {k: vars(v) for k, v in self.learner.models.items()},
            "predictions": self.predictor.snapshot(),
            "control": vars(self.control.decide(self.state, self.current_context())),
            "perception": {
                "system": self.last_system,
                "hardware": self.last_hardware,
                "screen": self.last_screen,
                "senses": self.last_senses,
            },
            "action": self.last_action,
            "dream_report": self.dream_last_report,
            "lifecycle": vars(self.lifecycle.state),
        }

    def tick(self):
        self.nervous.heartbeat("kernel", state="running", detail={"phase": self.lifecycle.state.phase.value})
        self.sync_phenotype()
        tick_event = self.emit(
            "tick.started",
            {"uptime": self.state.uptime},
            priority="background",
        )
        self.current_correlation = tick_event.event_id

        self.emit(
            "perception.request",
            {"domains": ["system", "hardware", "screen", "camera", "audio"]},
            priority="normal",
            correlation_id=self.current_correlation,
            target=self.perception_cell.name,
        )
        delivered = self.nervous.dispatch(256)

        self.emit(
            "heartbeat.request",
            {"tick": self.state.uptime},
            priority="background",
            correlation_id=self.current_correlation,
        )
        self.nervous.dispatch(64)

        snap = self.snapshot()
        snap["pipeline"] = {
            "correlation_id": self.current_correlation,
            "delivered_events": delivered,
        }
        (ROOT / "state/runtime.json").write_text(json.dumps(snap, indent=2))
        return snap

    def lifecycle_step(self):
        self.nervous.heartbeat("kernel", state="running", detail={"phase": self.lifecycle.state.phase.value})
        level, plugged = level_and_charging()
        previous = self.lifecycle.state.phase.value
        state = self.lifecycle.update_power(level, plugged)
        phase = state.phase.value
        self.nervous.set_phase(phase)

        self.emit(
            "lifecycle.transition",
            {
                "from": previous,
                "phase": phase,
                "battery": level,
                "charging": plugged,
                "reason": state.reason,
            },
            priority="control",
            provenance="power",
        )
        self.nervous.dispatch(128)

        if phase == "pre_sleep":
            self.lifecycle.enter_dream()
            dream_phase = self.lifecycle.state.phase.value
            self.nervous.set_phase(dream_phase)
            self.emit(
                "lifecycle.transition",
                {
                    "from": "pre_sleep",
                    "phase": dream_phase,
                    "battery": level,
                    "charging": plugged,
                    "reason": self.lifecycle.state.reason,
                },
                priority="control",
                provenance="power",
            )
            self.nervous.dispatch(128)
            self.dream_last_report = self.dream.consolidate(
                self.associative, self.learner
            )
            self.log.info("dream cycle %s complete", state.dream_cycles)

        elif phase == "wake":
            self.lifecycle.finish_wake()
            awake = self.lifecycle.state.phase.value
            self.nervous.set_phase(awake)
            self.emit(
                "lifecycle.transition",
                {
                    "from": "wake",
                    "phase": awake,
                    "battery": level,
                    "charging": plugged,
                    "reason": self.lifecycle.state.reason,
                },
                priority="control",
                provenance="power",
            )
            self.nervous.dispatch(128)
            self.log.info("wake transition: %s", state.reason)

        snap = self.snapshot()
        (ROOT / "state/runtime.json").write_text(json.dumps(snap, indent=2))
        return self.lifecycle.state

    def run(self):
        self.log.info("G.A.I. kernel starting")
        while True:
            phase = self.lifecycle_step().phase.value
            if phase == "awake":
                self.tick()
                time.sleep(self.cfg.get("tick_seconds", 2))
            elif phase == "dream":
                time.sleep(1.0)


if __name__ == "__main__":
    Kernel().run()
