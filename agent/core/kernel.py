



import json
import logging
import threading
import fcntl
import time
from pathlib import Path

from .state import InternalState
from .drives import DriveState
from .homeostasis import CoreNeeds
from .motivation import MotivationSystem
from .world import WorldState
from .memory import Memory
from .signals import SignalBus
from .control import ControlCentre
from .learning import OutcomeLearner, ExperiencePolicy
from .prediction import PredictiveModel
from .lifecycle import Lifecycle
from .dream import DreamEngine
from .evolution import EvolutionEngine
from .power import level_and_charging, PerformanceGovernor
from .sensory import SensoryDock
from .thoughts import ThoughtStream
from .scaling import compute_scale, effective_tick_fps, effective_metabolic_hz, worker_count, BASE_TICK_FPS
from .agent import LocalAgent
from .working_memory import WorkingMemoryCell
from cognition.core import CognitiveCore
from cognition.v1 import BabyBrain
from .cells import (
    PerceptionCell, MotivationCell, DriveCell, PredictionCell, ControlCell,
    ActionCell, MemoryCell, LifecycleCell, NervousSupervisor,
)
from .user_commands import UserCommandCell
from .motor_center import MotorActionCentre
from .neural_fabric import NeuralFabric
from .imagination import ImaginationPort
from .dream_tracker import DreamTracker
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
    def __init__(self, acquire_lock=True):
        self._lock_path = ROOT / "state/kernel.lock"
        self._lock_file = None
        if acquire_lock:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._lock_file = self._lock_path.open("w")
            try:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self._lock_file.close()
                self._lock_file = None
                raise SystemExit("G.A.I. kernel already running")
        cfg = json.loads(CONFIG.read_text())
        self.cfg = cfg
        self.state = InternalState()
        self.drives = DriveState()
        self.core_needs = CoreNeeds()
        self.motivation = MotivationSystem()
        self.performance_governor = PerformanceGovernor()
        self.sensory = SensoryDock()
        self.thoughts = ThoughtStream(self)
        self.latest_reward = 0.0
        self.world = WorldState()
        self.last_system = {}
        self.last_hardware = {}
        self.last_action = {"type": "none"}
        self.last_screen = {}
        self.last_senses = {}
        self.latest_prediction_error = 0.0
        self.latest_outcome_error = 0.0
        self.current_correlation = None
        self.user_action_request = None
        self.user_lifecycle_request = None
        self.physical_lifecycle_request = None
        self.metabolic_workers = self._load_metabolic_workers()
        self.tick_fps = self._load_tick_fps()
        self._tick_count = 0
        self._tick_window_start = time.perf_counter()
        self._tick_index = 0
        self._last_perception_time = 0.0
        self._last_runtime_snapshot = 0.0
        self._last_lifecycle_time = 0.0
        self._last_screen_perception_time = 0.0

        self.actions = SafeActions()
        self.senses = Senses()
        self.memory = Memory(cfg["memory_db"])
        self.associative = AssociativeMemory()
        self.semantic = SemanticNetwork()
        self.bus = SignalBus()
        # One experience/world model serves prediction, learning, and outcome attribution.
        self.learner = OutcomeLearner()
        self.experience_policy = ExperiencePolicy()
        self.predictor = self.learner
        self.nervous = self.bus.nervous

        self.control = ControlCentre(self.bus, self.learner)
        self.lifecycle = Lifecycle()
        self.evolution = EvolutionEngine()
        self.dream = DreamEngine(self.evolution)
        self.dream_tracker = DreamTracker()
        self.dream_last_report = None
        self.v1_brain = BabyBrain(self)
        self.neural_fabric = NeuralFabric()
        speed_path = ROOT / "state/simulation_speed.json"
        if not speed_path.exists():
            speed_path.write_text(json.dumps({"multiplier": float(cfg.get("simulation_speed_default", 1.0)), "timestamp": time.time(), "source": "config"}))

        self._running = True
        (ROOT / "state/gai_active.json").write_text(json.dumps({"active": True, "started": time.time()}))
        self._register_cells()
        self._start_persistent_organs()

        Path(cfg["log_file"]).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=cfg["log_file"],
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        self.log = logging.getLogger("gai")
        self.sync_phenotype()

    def _start_persistent_organs(self):
        if self._lock_file is None:
            return
        import os, subprocess
        env=dict(os.environ); env.setdefault('DISPLAY',':0'); env.setdefault('XAUTHORITY','/home/null/.Xauthority'); env.setdefault('XDG_RUNTIME_DIR','/run/user/1000'); env.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path=/run/user/1000/bus')
        self._persistent_pid_files = {
            'speaker': ROOT/'state/speaker_organ.pid',
            'screen_stream': ROOT/'state/screen_stream.pid',
            'focus_bubble': ROOT/'state/focus_bubble.pid',
            'display_guard': ROOT/'state/display_guard.pid',
            'lid_guard': ROOT/'state/lid_guard.pid',
        }
        processes = {
            'speaker': ROOT/'agent/gui/speaker_organ.py',
            'screen_stream': ROOT/'agent/perception/screen_stream.py',
            'focus_bubble': ROOT/'agent/gui/focus_bubble.py',
            'display_guard': ROOT/'agent/gui/display_guard.py',
            'lid_guard': ROOT/'agent/core/lid_guard.py',
        }
        for organ, path in processes.items():
            pidfile=self._persistent_pid_files[organ]; alive=False
            try:
                pid=int(pidfile.read_text().strip()); os.kill(pid,0); alive=True
            except Exception: pass
            if not alive:
                p=subprocess.Popen([str(ROOT/'venvs/gai/bin/python'),str(path)],
                                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
                pidfile.parent.mkdir(parents=True,exist_ok=True); pidfile.write_text(str(p.pid))
                self.nervous.publish('organ.output.ready',{'organ':organ,'pid':p.pid,'persistent':True},
                                     source='kernel',priority='control')

    def _stop_persistent_organs(self):
        import os, signal
        for pidfile in getattr(self,'_persistent_pid_files',{}).values():
            try:
                pid=int(pidfile.read_text().strip()); os.kill(pid,signal.SIGTERM)
            except Exception: pass
            try: pidfile.unlink()
            except Exception: pass

    def _register_cells(self):
        self.agent = LocalAgent(self)
        self.nervous.register_component(
            "kernel", kind="core", version="0.2.0", sleep_capable=False, critical=True
        )
        self.user_command_cell = UserCommandCell(self).start()
        self.perception_cell = PerceptionCell(self).start()
        self.motivation_cell = MotivationCell(self).start()
        self.drive_cell = DriveCell(self).start()
        self.prediction_cell = PredictionCell(self).start()
        self.control_cell = ControlCell(self).start()
        self.action_cell = ActionCell(self).start()
        self.motor_action = MotorActionCentre(self).start()
        self.imagination = ImaginationPort(self).start()
        self.memory_cell = MemoryCell(self).start()
        self.working_memory = WorkingMemoryCell(self.nervous).start()

        active = [
            self.perception_cell,
            self.motivation_cell,
            self.drive_cell,
            self.prediction_cell,
            self.control_cell,
            self.action_cell,
        ]
        self.lifecycle_cell = LifecycleCell(self, active).start()
        self.supervisor = NervousSupervisor(self).start()
        self.cognitive_core = CognitiveCore(
            nervous=self.nervous,
            memory=self.memory,
            model=None,
            fallback=self._v1_model,
        )
        self.cells = [
            self.user_command_cell, self.perception_cell, self.motivation_cell, self.drive_cell, self.prediction_cell,
            self.control_cell, self.action_cell, self.memory_cell,
            self.working_memory, self.lifecycle_cell, self.supervisor,
        ]

    def _v1_model(self, prompt):
        return self.v1_brain.decide()

    def _simulation_speed(self):
        try:
            obj = json.loads((ROOT / "state/simulation_speed.json").read_text())
            return max(0.1, min(10.0, float(obj.get("multiplier", 1.0))))
        except Exception:
            return 1.0

    def _load_metabolic_workers(self):
        return worker_count(self.cfg)

    def _max_tick_fps(self):
        return max(BASE_TICK_FPS, effective_tick_fps(self.cfg, 1.0))

    def _load_tick_fps(self):
        return max(BASE_TICK_FPS, effective_tick_fps(self.cfg, 1.0))

    def _refresh_tick_rate(self):
        self.metabolic_workers = worker_count(self.cfg)
        self.tick_fps = effective_tick_fps(self.cfg, self._simulation_speed())

    def sync_phenotype(self):
        genes = self.evolution.phenotype()
        self.learner.learning_rate = genes["prediction_lr"]
        self.associative.association_gain = genes["association_gain"]
        self.control.params = genes

    def drive_values(self):
        return {
            "curiosity": self.state.curiosity,
            "satisfaction": self.state.satisfaction,
            "safety": self.state.stress,
            "energy": 1.0 - self.state.energy,
            "boredom": self.state.boredom,
            "social": self.core_needs.social,
        }

    def appearance_snapshot(self):
        """Translate internal state into a bounded, autonomous visual phenotype."""
        emotions = self.motivation.emotions
        curiosity = max(0.0, min(1.0, float(getattr(emotions, "curiosity", self.state.curiosity))))
        satisfaction = max(0.0, min(1.0, float(getattr(emotions, "satisfaction", self.state.satisfaction))))
        fear = max(0.0, min(1.0, float(getattr(emotions, "fear", 0.0))))
        stress = max(0.0, min(1.0, float(getattr(emotions, "stress", self.state.stress))))
        fatigue = max(0.0, min(1.0, float(getattr(emotions, "fatigue", self.state.fatigue))))
        happiness = max(-1.0, min(1.0, float(self.state.happiness)))
        boredom = max(0.0, min(1.0, float(self.state.boredom)))
        sleep_need = max(0.0, min(1.0, float(self.core_needs.sleep_need)))
        phase = self.lifecycle.state.phase.value
        override = self.cfg.get("appearance", {}) or {}
        requested = str(override.get("style", "auto")).lower()
        if requested != "auto":
            style = requested
        elif phase == "dream":
            style = "dream"
        elif stress > .72 or fear > .72:
            style = "alert"
        elif curiosity > .72:
            style = "curious"
        elif satisfaction > .72:
            style = "warm"
        elif fatigue > .72:
            style = "quiet"
        else:
            style = "minimal"
        # Dream cycles give the visual phenotype a slow-changing identity.
        variant = int(self.lifecycle.state.dream_cycles) % 6
        return {
            "style": style,
            "variant": variant,
            "curiosity": round(curiosity, 3),
            "satisfaction": round(satisfaction, 3),
            "fear": round(fear, 3),
            "stress": round(stress, 3),
            "fatigue": round(fatigue, 3),
            "happiness": round(happiness, 3),
            "boredom": round(boredom, 3),
            "sleep_need": round(sleep_need, 3),
            "phase": phase,
            "mode": self.state.mode,
        }

    def current_context(self):
        vision = self.last_senses.get("vision") or {}
        concepts = vision.get("concepts", [])
        context = ["camera" if self.last_senses.get("camera") else "no_camera"]
        context.extend(concepts[:16])
        audio = self.last_senses.get("audio") or {}
        if isinstance(audio, dict) and float(audio.get("rms", 0.0)) > .03:
            context.append("sound")
        attention_path = ROOT / "state/attention.json"
        try:
            attention = json.loads(attention_path.read_text()).get("selected", {})
            if attention.get("target"):
                context.append(f"attention:{attention.get('modality')}:{attention.get('target')}")
        except Exception:
            pass
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
            "core_needs": self.core_needs.snapshot(),
            "motivation": self.motivation.snapshot(),
            "performance": self.performance_governor.snapshot(),
            "sensory": self.sensory.snapshot(),
            "thoughts": self.thoughts.snapshot(),
            "drives": vars(self.drives),
            "world": vars(self.world),
            "latest_reward": self.latest_reward,
            "latest_prediction_error": self.latest_prediction_error,
            "latest_outcome_error": self.latest_outcome_error,
            "memory_budget": self.memory.budget_snapshot() if hasattr(self.memory, "budget_snapshot") else {},
            "signals": self.bus.snapshot(),
            "learning": self.bus.learning_snapshot(),
            "nervous": self.bus.nervous_snapshot(),
            "working_memory": self.working_memory.snapshot(),
            "outcome_model": {k: vars(v) for k, v in self.learner.models.items()},
            "predictions": self.predictor.snapshot(),
            "control": (
                {"mode": "v1", "legacy_controller_disabled": True}
                if bool(self.cfg.get("v1_mode", False))
                else vars(self.control.decide(self.state, self.current_context()))
            ),
            "perception": {
                "system": self.last_system,
                "hardware": self.last_hardware,
                "screen": self.last_screen,
                "senses": self.last_senses,
            },
            "action": self.last_action,
            "v1": {
                "speed_multiplier": self._simulation_speed(),
                **self.v1_brain.snapshot(),
            },
            "dream_report": self.dream_last_report,
            "dream_tracker": self.dream_tracker.snapshot(),
            "sleep_session": self.lifecycle.snapshot(),
            "neural_fabric": self.neural_fabric.snapshot(),
            "appearance": self.appearance_snapshot(),
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

        self._tick_index += 1
        now = time.perf_counter()
        # One biological clock: vision is sampled once per CNS tick.
        # Audio capture remains continuous infrastructure; its compressed state is
        # consumed here at the same biological tick as vision and cognition.
        perception_hz = max(0.1, self.tick_fps)
        do_perception = (now - self._last_perception_time) >= (1.0 / perception_hz)
        if do_perception:
            self._last_perception_time = now
            self.emit(
                "perception.request",
                {"domains": ["system", "hardware", "screen", "camera", "audio"]},
                priority="normal",
                correlation_id=self.current_correlation,
                target=self.perception_cell.name,
            )
        t_perception = time.perf_counter()
        delivered = self.nervous.dispatch(128)
        t_dispatch = time.perf_counter()
        if not bool(self.cfg.get("v1_mode", False)):
            self.thoughts.tick()

        # V1: one kernel tick is one complete CNS/CC decision opportunity.
        if bool(self.cfg.get("v1_mode", False)) and self.lifecycle.state.phase.value == "awake":
            # Neural layer is the intermediary: ingest compressed senses, select attention,
            # then publish the neural workspace before CC reasons.
            vision = (self.last_senses.get("vision") or {}) if isinstance(self.last_senses, dict) else {}
            temporal = vision.get("temporal") or {}
            self.neural_fabric.ingest({"source":"sight","modality":"vision","salience":temporal.get("salience",0.0),"novelty":vision.get("sensory_novelty",0.0)})
            audio = (self.last_senses.get("audio") or {}) if isinstance(self.last_senses, dict) else {}
            auditory = audio.get("auditory") or {}
            self.neural_fabric.ingest({"source":"hearing","modality":"audio","salience":min(1.0,float(auditory.get("rms",0.0) or 0.0)*8.0)})
            self.neural_attention = self.neural_fabric.select_attention(self.last_senses)
            self.nervous.publish("neural.workspace", {"attention":self.neural_attention}, source="neural_fabric", priority="control", correlation_id=self.current_correlation)
            self.nervous.dispatch(32)
            self.cognitive_core.think("awake", correlation_id=self.current_correlation)
            t_cognition = time.perf_counter()
            self.nervous.dispatch(128)
            t_post = time.perf_counter()
            try:
                decision = self.v1_brain.last_decision or {}
                attention = (decision.get("attention") or {}).get("selected") or {}
                action = (decision.get("intention") or {}).get("type", "wait")
                result = (self.last_action or {}).get("result") or {}
                outcome_reward = 0.65 if result.get("success") is True else (-0.30 if result.get("success") is False else (0.10 if action not in {"wait","rest"} else 0.0))
                self.neural_fabric.route(attention, action, outcome_reward, self.latest_prediction_error)
            except Exception:
                pass
            self.emit("tick.completed", {"action": self.last_action, "cycle": self.v1_brain.cycle}, priority="background", correlation_id=self.current_correlation, provenance="kernel")
            self.nervous.dispatch(32)
            t_end_pipeline = time.perf_counter()
        else:
            t_cognition = t_post = t_end_pipeline = time.perf_counter()

        self._last_tick_timings = {
            "dispatch_ms": round((t_dispatch-t_perception)*1000,1),
            "cognition_ms": round((t_cognition-t_dispatch)*1000,1),
            "post_cognition_ms": round((t_post-t_cognition)*1000,1),
            "pipeline_tail_ms": round((t_end_pipeline-t_post)*1000,1),
        }
        self.emit(
            "heartbeat.request",
            {"tick": self.state.uptime},
            priority="background",
            correlation_id=self.current_correlation,
        )
        self.nervous.dispatch(64)

        self._tick_count += 1
        now = time.perf_counter()
        elapsed = now - self._tick_window_start
        if elapsed >= 1.0:
            self._tick_rate = self._tick_count / elapsed
            self._tick_count = 0
            self._tick_window_start = now
        runtime_hz = max(0.25, float(self.cfg.get("runtime_snapshot_hz", 1)))
        runtime_due = now - self._last_runtime_snapshot >= (1.0 / runtime_hz)
        if runtime_due:
            self._last_runtime_snapshot = now
            snap = self.snapshot()
            snap["tick"] = {"base_fps": BASE_TICK_FPS,
                             "target_fps": round(self.tick_fps, 3),
                             "actual_fps": round(getattr(self, "_tick_rate", 0.0), 1),
                             "simulation_speed": self._simulation_speed(),
                             "compute_scale": compute_scale(self.cfg),
                             "metabolic_hz": round(effective_metabolic_hz(self.cfg, self._simulation_speed()), 3),
                             "metabolic_workers": self.metabolic_workers,
                             "metabolic_ceiling": self._max_tick_fps()}
            snap["scheduler"] = {"tick_index": self._tick_index, "perception_hz": perception_hz, "perception_due": do_perception,
                                   "timings_ms": {"dispatch": round((t_dispatch-t_perception)*1000,1),
                                                  "cognition": round((t_cognition-t_dispatch)*1000,1),
                                                  "post_cognition": round((t_post-t_cognition)*1000,1),
                                                  "pipeline_tail": round((t_end_pipeline-t_post)*1000,1)}}
            snap["pipeline"] = {
                "correlation_id": self.current_correlation,
                "delivered_events": delivered,
            }
            (ROOT / "state/runtime.json").write_text(json.dumps(snap, indent=2))
            return snap
        return None

    def lifecycle_step(self):
        self.nervous.heartbeat("kernel", state="running", detail={"phase": self.lifecycle.state.phase.value})
        level, plugged = level_and_charging()
        previous = self.lifecycle.state.phase.value
        memory_pipeline_pressure = self.memory_pipeline.pressure() if hasattr(self, "memory_pipeline") else 0.0
        persistent_memory_pressure = float(self.memory.budget_snapshot().get("usage", 0.0))
        memory_pressure = max(memory_pipeline_pressure, persistent_memory_pressure)
        self.lifecycle.metabolic_workers = self.metabolic_workers
        state = self.lifecycle.update_power(
            level,
            plugged,
            energy=self.core_needs.energy,
            fatigue=self.motivation.emotions.fatigue,
            memory_pressure=memory_pressure,
            v1_mode=bool(self.cfg.get("v1_mode", False)),
        )
        phase = state.phase.value
        suspend_result_path = ROOT / "state/physical_suspend_result.json"
        try:
            if suspend_result_path.exists() and self.lifecycle.sleep_cycle.session:
                result = json.loads(suspend_result_path.read_text())
                self.lifecycle.sleep_cycle.mark_suspend(
                    attempted=True, completed=bool(result.get("completed"))
                )
                self.dream_tracker.event(
                    "physical_suspend_result",
                    self.lifecycle.sleep_cycle.session,
                    completed=bool(result.get("completed")),
                    nvidia_suspend_failure=bool(result.get("nvidia_suspend_failure")),
                    elapsed_seconds=result.get("elapsed_seconds"),
                )
                suspend_result_path.unlink()
        except Exception:
            pass

        physical_request = None
        physical_path = ROOT / "state/physical_lifecycle_request.json"
        try:
            if physical_path.exists():
                physical_request = json.loads(physical_path.read_text())
                physical_path.unlink()
        except Exception:
            physical_request = None
        if isinstance(physical_request, dict):
            command = str(physical_request.get("command", ""))
            if command == "sleep" and not state.physical_sleep_latched:
                reason = str(physical_request.get("reason", "physical lid closed"))
                session = self.lifecycle.begin_sleep_session(reason, physical=True)
                state = self.lifecycle.state
                phase = "pre_sleep"
                state.physical_sleep_latched = True
                self.dream_tracker.stage("pre_sleep", session, reason=reason, physical=True)
                self.emit("physiology.lid_closed", {"reason": reason, "non_vetoable": True, "sleep_session": session.id}, priority="control", provenance="physical_body")
                self.neural_fabric.begin_physical_sleep(reason)
            elif command == "wake" and phase != "awake":
                reason = str(physical_request.get("reason", "physical lid opened"))
                session = self.lifecycle.request_wake(reason)
                self.dream_tracker.event("wake_requested", session, reason=reason, physical=True)
                self.emit("physiology.lid_opened", {"reason": reason}, priority="control", provenance="physical_body")
                if self.lifecycle.sleep_cycle.can_wake():
                    state.phase = type(state.phase).WAKE
                    state.reason = reason
                    phase = "wake"
                    state.physical_sleep_latched = False
                    self.neural_fabric.end_physical_sleep(reason)
        user_lifecycle = getattr(self, "user_lifecycle_request", None)
        if isinstance(user_lifecycle, dict):
            command = str(user_lifecycle.get("command", ""))
            if command == "sleep" and phase == "awake":
                reason = str(user_lifecycle.get("reason", "accepted user sleep request"))
                session = self.lifecycle.begin_sleep_session(reason, physical=False)
                state = self.lifecycle.state
                phase = "pre_sleep"
                self.dream_tracker.stage("pre_sleep", session, reason=reason, physical=False)
            elif command == "wake" and phase != "awake":
                reason = str(user_lifecycle.get("reason", "accepted user wake request"))
                session = self.lifecycle.request_wake(reason)
                self.dream_tracker.event("wake_requested", session, reason=reason, physical=False)
                if self.lifecycle.sleep_cycle.can_wake():
                    state.phase = type(state.phase).WAKE
                    state.reason = reason
                    phase = "wake"
            self.user_lifecycle_request = None
        # A wake request does not instantly restore waking consciousness. One
        # lifecycle step is reserved for sleep exit/wake recovery.
        if phase == "dream" and self.lifecycle.sleep_cycle.can_wake():
            state.phase = type(state.phase).WAKE
            state.reason = self.lifecycle.sleep_cycle.session.wake_reason
            phase = "wake"
            state.physical_sleep_latched = False
            self.neural_fabric.end_physical_sleep(state.reason)
        if phase == "wake" and state.reason == "wake_recovery":
            self.lifecycle.complete_wake()
            state = self.lifecycle.state
            phase = state.phase.value
            self.dream_tracker.stage("awake", self.lifecycle.sleep_cycle.session, reason="wake_recovery_complete")

        self.neural_fabric.set_phase(phase)
        if phase == "pre_sleep":
            self.neural_fabric.maintenance()
        self.sensory.set_phase(phase, self.motivation.emotions.fatigue)
        # Physical sensory organs follow lifecycle power state: disconnected/sleeping
        # organs are released and produce no input until the organism wakes.
        if phase == "awake":
            self.senses.camera.open()
        else:
            self.senses.camera.close()
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
            session = self.lifecycle.sleep_cycle.session
            self.dream_tracker.stage("sleep_entry", session)
            self.dream_tracker.stage("deep_sleep", session)
            self.dream_tracker.stage("dream", session, neural_generation=self.neural_fabric.generation)
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
            self.dream_last_report = self.dream.run_cycle(
                self.associative, self.learner, self.neural_fabric
            )
            self.lifecycle.sleep_cycle.mark_consolidated()
            self.dream_tracker.event("consolidation_complete", session,
                                     events=self.dream_last_report.get("events", 0),
                                     changes=self.dream_last_report.get("changes", 0))
            self.neural_fabric.set_phase("dream")
            self.log.info("dream cycle %s complete", state.dream_cycles)

        elif phase == "wake":
            session = self.lifecycle.sleep_cycle.session
            self.dream_tracker.stage("sleep_exit", session, reason=self.lifecycle.state.reason)
            self.lifecycle.finish_wake()
            self.dream_tracker.stage("wake_recovery", session)
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

        # Lifecycle runs independently from the biological clock. Do not serialize
        # the full organism snapshot here; the tick owns runtime telemetry. This
        # avoids duplicate 200KB+ JSON writes every 0.5s while awake.
        return self.lifecycle.state

    def close(self):
        """Release physical organs owned by this kernel instance."""
        self._running = False
        try:
            if hasattr(self, "motor_action"):
                self.motor_action.close()
        except Exception:
            pass
        try:
            self._stop_persistent_organs()
        except Exception:
            pass
        try:
            (ROOT / "state/gai_active.json").write_text(json.dumps({"active": False, "stopped": time.time()}))
        except Exception:
            pass
        try:
            if hasattr(self, "agent") and hasattr(self.agent, "audio_input"):
                self.agent.audio_input.stop()
        except Exception:
            pass
        try:
            if self._lock_file is not None:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
                self._lock_file = None
        except Exception:
            pass

    def run(self):
        self.log.info("G.A.I. kernel starting")
        while True:
            now = time.perf_counter()
            if now - self._last_lifecycle_time >= 0.5:
                self._last_lifecycle_time = now
                phase = self.lifecycle_step().phase.value
            else:
                phase = self.lifecycle.state.phase.value
            if phase == "awake":
                self._refresh_tick_rate()
                self.lifecycle.clock_tick()
                frame_start = time.perf_counter()
                self.tick()
                effective_fps = max(0.1, self.tick_fps)
                frame_time = 1.0 / effective_fps
                remaining = frame_time - (time.perf_counter() - frame_start)
                if remaining > 0:
                    time.sleep(remaining)
            elif phase == "dream":
                self.lifecycle.clock_tick()
                time.sleep(1.0 / max(1.0, self.tick_fps))


if __name__ == "__main__":
    Kernel().run()
