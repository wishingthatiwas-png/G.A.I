from __future__ import annotations

from .cell import Cell
from .nervous import Event


class PerceptionCell(Cell):
    def __init__(self, kernel):
        super().__init__("perception", kernel.nervous, version="0.2.0", sleep_phases={"awake"}, critical=True)
        self.kernel = kernel
        self.listen("perception.request", self.receive, {"awake"})

    def receive(self, event: Event):
        self.kernel.state.update_time()
        k = self.kernel
        k.last_system = k.system_snapshot()
        k.last_hardware = k.hardware_snapshot()
        k.last_screen = k.screen_snapshot()
        k.last_senses = k.senses.observe()
        perception = {"system": k.last_system, "hardware": k.last_hardware, "screen": k.last_screen, "senses": k.last_senses}
        k.world.observe(perception)
        self.heartbeat({"observation_count": k.world.observation_count})
        k.emit("perception.observation", {
            "perception": perception,
            "camera": bool(k.last_senses.get("camera")),
            "concepts": (k.last_senses.get("vision") or {}).get("concepts", [])
        }, priority="normal", correlation_id=event.correlation_id, provenance="sensor",
           confidence=1.0, novelty=k.perception_novelty())


class DriveCell(Cell):
    def __init__(self, kernel):
        super().__init__("drives", kernel.nervous, version="0.2.0", sleep_phases={"awake"}, critical=True)
        self.kernel = kernel
        self.listen("perception.observation", self.receive, {"awake"})

    def receive(self, event: Event):
        k = self.kernel
        perception = event.payload["perception"]
        k.drives.update(k.state, perception)
        load = float(k.last_system.get("load_1m", 0.0))
        memory = float(k.last_system.get("memory_percent", 0.0)) / 100.0
        audio = k.last_senses.get("audio") or {}
        rms = float(audio.get("rms", 0.0)) if isinstance(audio, dict) else 0.0
        novelty = float(event.novelty)
        k.bus.publish("fatigue", k.state.fatigue, adaptive=True, source="drives")
        k.bus.publish("threat", min(1.0, load / 2.0 + memory * .25), adaptive=True, source="drives")
        k.bus.publish("novelty", novelty, adaptive=True, source="drives")
        k.bus.publish("curiosity", k.state.curiosity, adaptive=True, source="drives")
        k.bus.publish("interaction", .65 if rms > .03 else 0.0, adaptive=True, source="drives")
        k.bus.publish("maintenance", min(1.0, load / 2.0 + memory * .5), adaptive=True, source="drives")
        self.heartbeat({"strongest": k.drives.strongest()})
        k.emit("drive.update", k.drive_values(), priority="control",
               correlation_id=event.correlation_id, provenance="internal")


class PredictionCell(Cell):
    def __init__(self, kernel):
        super().__init__("prediction", kernel.nervous, version="0.2.0", sleep_phases={"awake"}, critical=True)
        self.kernel = kernel
        self.listen("drive.update", self.receive, {"awake"})

    def receive(self, event: Event):
        k = self.kernel
        actual = k.drive_values()
        prediction_error = k.predictor.observe(actual)
        outcome_error = k.learner.observe(actual)
        k.latest_prediction_error = prediction_error
        k.latest_outcome_error = outcome_error
        self.heartbeat({"prediction_error": prediction_error, "outcome_error": outcome_error})
        k.emit("prediction.error", {"value": prediction_error, "outcome_error": outcome_error},
               priority="control", correlation_id=event.correlation_id, provenance="learned")


class ControlCell(Cell):
    def __init__(self, kernel):
        super().__init__("control", kernel.nervous, version="0.2.0", sleep_phases={"awake"}, critical=True)
        self.kernel = kernel
        self.listen("prediction.error", self.receive, {"awake"})

    def receive(self, event: Event):
        k = self.kernel
        context = k.current_context()
        decision = k.control.decide(k.state, context)
        self.heartbeat({"action": decision.action, "score": decision.score})
        k.emit("control.decision", {
            "action": decision.action, "score": decision.score,
            "expected_reward": decision.expected_reward, "reason": decision.reason,
            "context": context
        }, priority="control", correlation_id=event.correlation_id, provenance="predicted")
        k.emit("action.request", {
            "action": decision.action, "reason": decision.reason,
            "expected_reward": decision.expected_reward, "context": context,
            "score": decision.score
        }, priority="control", correlation_id=event.correlation_id, provenance="controller")


class ActionCell(Cell):
    def __init__(self, kernel):
        super().__init__("actions", kernel.nervous, version="0.2.0", sleep_phases={"awake"}, critical=True)
        self.kernel = kernel
        self.listen("action.request", self.receive, {"awake"})

    def receive(self, event: Event):
        k = self.kernel
        p = event.payload
        action = p["action"]
        context = p.get("context") or k.current_context()
        k.state.mode = action
        predicted = k.predictor.choose(action, context, k.drive_values())
        k.learner.choose(action)
        k.last_action = {
            "type": action,
            "reason": p.get("reason", ""),
            "score": float(p.get("score", 0.0)),
            "expected_reward": float(p.get("expected_reward", 0.0)),
            "prediction_error": float(k.latest_prediction_error),
            "outcome_error": float(k.latest_outcome_error)
        }
        perception = {"system": k.last_system, "hardware": k.last_hardware,
                      "screen": k.last_screen, "senses": k.last_senses}
        concepts = (k.last_senses.get("vision") or {}).get("concepts", [])
        stimuli = ["system", "camera_present" if k.last_senses.get("camera") else "camera_absent", action]
        stimuli.extend(concepts[:24])
        audio = k.last_senses.get("audio") or {}
        rms = float(audio.get("rms", 0.0)) if isinstance(audio, dict) else 0.0
        if rms > .03:
            stimuli.append("sound_present")
        emotions = {"curiosity": k.state.curiosity, "stress": k.state.stress,
                    "satisfaction": k.state.satisfaction, "fatigue": k.state.fatigue}
        reward = k.state.satisfaction - k.state.stress
        k.actions.save_observation(perception)
        k.associative.fire(stimuli, emotions=emotions,
                           context={"action": k.last_action, "observation": k.world.observation_count},
                           reward=reward)
        k.emit("reward.signal", {"value": reward, "drives": k.drive_values(), "action": action},
               priority="control", correlation_id=event.correlation_id, provenance="internal")
        k.emit("memory.enqueued", {
            "stimuli": stimuli, "reward": reward,
            "prediction_error": k.latest_prediction_error,
            "action": k.last_action, "context": context, "perception": perception
        }, priority="background", correlation_id=event.correlation_id, provenance="experience")
        k.emit("action.completed", {"action": action, "predicted": predicted},
               priority="normal", correlation_id=event.correlation_id, provenance="action")
        k.emit("tick.completed", {"action": action, "prediction_error": k.latest_prediction_error},
               priority="background", correlation_id=event.correlation_id, provenance="kernel")
        self.heartbeat({"action": action, "reward": reward, "prediction_error": k.latest_prediction_error})


class MemoryCell(Cell):
    def __init__(self, kernel):
        super().__init__("memory", kernel.nervous, version="0.2.0",
                         sleep_phases={"awake", "pre_sleep", "dream", "wake"})
        self.kernel = kernel
        self.listen("memory.enqueued", self.receive, self.sleep_phases)

    def receive(self, event: Event):
        k = self.kernel
        p = event.payload
        k.memory.remember("tick", {
            "mode": k.state.mode,
            "drives": vars(k.drives),
            "action": p.get("action", k.last_action),
            "signals": k.bus.snapshot(),
            "stimuli": p.get("stimuli", []),
            "context": p.get("context", [])
        })
        self.heartbeat({"saved": True, "observation": k.world.observation_count})


class LifecycleCell(Cell):
    def __init__(self, kernel, cells):
        super().__init__("lifecycle", kernel.nervous, version="0.2.0",
                         sleep_phases={"awake", "pre_sleep", "dream", "wake"})
        self.kernel = kernel
        self.cells = cells
        self.listen("lifecycle.transition", self.receive, self.sleep_phases)

    def receive(self, event: Event):
        phase = event.payload.get("phase", self.kernel.lifecycle.state.phase.value)
        for cell in self.cells:
            if phase in {"dream", "pre_sleep"} and cell.started:
                cell.sleep()
            elif phase in {"awake", "wake"} and cell.started:
                cell.wake()
        self.heartbeat({"phase": phase})


class NervousSupervisor(Cell):
    def __init__(self, kernel):
        super().__init__("supervisor", kernel.nervous, version="0.2.0",
                         sleep_phases={"awake", "pre_sleep", "dream", "wake"}, critical=True)
        self.kernel = kernel
        self.listen("heartbeat.request", self.receive, self.sleep_phases)

    def receive(self, event: Event):
        health = self.kernel.nervous.health()
        if health["critical_stale"]:
            self.kernel.emit("system.fault",
                             {"kind": "critical_stale", "components": health["critical_stale"]},
                             priority="critical", correlation_id=event.correlation_id,
                             provenance="supervisor")
        self.heartbeat({"ok": health["ok"], "critical_stale": health["critical_stale"]})
