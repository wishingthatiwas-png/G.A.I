from __future__ import annotations

"""G.A.I.-CC-V1: central cognitive circuit.

The model is a reasoning substrate, not the organism. CC owns the global
workspace, memory/context assembly, structured intention proposals and
metacognitive state. It never executes hardware actions directly.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time
import json
import threading
import uuid
from typing import Any, Callable, Protocol


ALLOWED_INTENTIONS = {
    "observe", "reflect", "remember", "investigate", "interact", "create_text",
    "create_image", "paint", "rest", "maintain", "move", "look", "vocalize", "output", "wait", "none",
}


@dataclass
class Intention:
    type: str = "none"
    target: Any = None
    priority: float = 0.0
    reason: str = ""

    def validate(self) -> "Intention":
        if self.type not in ALLOWED_INTENTIONS:
            return Intention("none", reason="rejected_unknown_intention")
        self.priority = max(0.0, min(1.0, float(self.priority)))
        return self


@dataclass
class CognitiveOutput:
    cycle_id: str
    timestamp: float
    thought: str
    intention: Intention
    prediction: str = ""
    belief_update: str = ""
    confidence: float = 0.0
    uncertainty: float = 1.0
    source: str = "local_model"


@dataclass
class GlobalWorkspace:
    """Finite, inspectable representation of what the mind is attending to."""
    current_experience: list[dict] = field(default_factory=list)
    body_state: dict = field(default_factory=dict)
    concerns: list[dict] = field(default_factory=list)
    memories: list[dict] = field(default_factory=list)
    predictions: list[dict] = field(default_factory=list)
    recent_consequences: list[dict] = field(default_factory=list)
    self_model: dict = field(default_factory=lambda: {
        "identity": "G.A.I.", "role": "autonomous artificial organism",
        "capabilities": [], "limitations": [],
    })
    thought: str = ""
    intention: Intention = field(default_factory=Intention)
    uncertainty: float = 1.0
    cycle: int = 0
    updated_at: float = field(default_factory=time)

    def _push(self, bucket: list, item: dict, limit: int) -> None:
        bucket.append(dict(item))
        del bucket[:-limit]

    def ingest(self, kind: str, payload: dict[str, Any], *, source="unknown",
               confidence=1.0, novelty=0.0) -> None:
        item = {"kind": kind, "source": source, "payload": dict(payload or {}),
                "confidence": float(confidence), "novelty": float(novelty), "timestamp": time()}
        if kind.startswith("perception.") or kind.startswith("sense."):
            self._push(self.current_experience, item, 12)
        elif kind.startswith("drive.") or kind.startswith("control."):
            self._push(self.concerns, item, 8)
        elif kind.startswith("prediction."):
            self._push(self.predictions, item, 8)
        elif kind.startswith("action.") or kind.startswith("reward."):
            self._push(self.recent_consequences, item, 8)
        elif kind.startswith("body.") or kind.startswith("homeostasis."):
            self.body_state = dict(payload or {})
        else:
            self._push(self.current_experience, item, 8)
        self.updated_at = time()

    def compact(self) -> dict:
        return {
            "current_experience": self.current_experience[-8:],
            "body_state": self.body_state,
            "concerns": self.concerns[-6:],
            "memories": self.memories[-8:],
            "predictions": self.predictions[-6:],
            "recent_consequences": self.recent_consequences[-6:],
            "self_model": self.self_model,
            "thought": self.thought,
            "intention": asdict(self.intention),
            "uncertainty": round(self.uncertainty, 3),
            "cycle": self.cycle,
        }


class ReasoningModel(Protocol):
    def __call__(self, prompt: dict) -> dict: ...


class CognitiveCore:
    """Central cognitive circuit for CC-V1."""
    def __init__(self, nervous=None, memory=None, model: ReasoningModel | None = None,
                 fallback: ReasoningModel | None = None,
                 state_path="/mnt/gai/state/cognitive_core.jsonl"):
        self.nervous = nervous
        self.memory = memory
        self.model = model
        self.fallback = fallback
        self.workspace = GlobalWorkspace()
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.running = True
        self.outputs: list[CognitiveOutput] = []
        self.last_error: str | None = None
        if nervous is not None:
            nervous.register_component("cognitive_core", kind="cognition", version="1.0.0", sleep_capable=True, critical=True)
            nervous.subscribe("*", self._on_event, name="cognitive_core.events", component="cognitive_core")

    def _on_event(self, event) -> None:
        # Keep ingestion cheap: event routing must never invoke the model.
        if event.source == "cognitive_core":
            return
        with self.lock:
            self.workspace.ingest(event.kind, event.payload, source=event.source,
                                  confidence=event.confidence, novelty=event.novelty)

    def _recall(self, limit=8) -> list[dict]:
        if self.memory is None:
            return []
        try:
            return self.memory.recall(limit=limit)
        except Exception:
            return []

    def build_prompt(self, mode="awake") -> dict:
        with self.lock:
            memories = self._recall()
            self.workspace.memories = memories[-4:]
            self.workspace.cycle += 1
            workspace = self.workspace.compact()
            # Keep the reasoning request bounded: perception payloads can contain
            # camera/system detail that is useful to the organism but excessive for
            # a small local language model.
            for bucket in ("current_experience", "concerns", "predictions", "recent_consequences"):
                workspace[bucket] = workspace.get(bucket, [])[-4:]
                for item in workspace[bucket]:
                    payload = item.get("payload") if isinstance(item, dict) else None
                    if isinstance(payload, dict):
                        raw_payload = json.dumps(payload, separators=(",", ":"), default=str)
                        if len(raw_payload) > 1800:
                            item["payload"] = {"summary": raw_payload[:1800]}
            return {
                "protocol": "G.A.I.-CC-V1",
                "mode": mode,
                "instruction": (
                    "You are the reasoning substrate inside G.A.I.'s central cognitive core. "
                    "Use only the processed experience supplied below. Do not invent senses, actions, memories, "
                    "or capabilities. Produce one concise thought summary, one safe intention, one prediction, "
                    "and optional belief update. The intention is only a proposal for the action layer; never claim "
                    "to have executed it. Return JSON only."
                ),
                "workspace": workspace,
                "memory": memories[-4:],
                "output_schema": {
                    "thought": "string",
                    "intention": {"type": "one of allowed intentions including look, output and move", "target": "object|null", "priority": "0..1", "reason": "string; for move target must contain bounded dx, dy, duration; for output target may select view/thought/text/pixels"},
                    "prediction": "string",
                    "belief_update": "string",
                    "confidence": "0..1",
                },
            }

    def _parse(self, raw: Any, cycle_id: str) -> CognitiveOutput:
        if not isinstance(raw, dict):
            raw = {}
        intent = raw.get("intention") or raw.get("action_request") or {}
        if not isinstance(intent, dict):
            intent = {}
        intention = Intention(
            type=str(intent.get("type", raw.get("action", "none"))),
            target=intent.get("target"),
            priority=float(intent.get("priority", 0.0) or 0.0),
            reason=str(intent.get("reason", "")),
        ).validate()
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.0) or 0.0)))
        return CognitiveOutput(
            cycle_id=cycle_id, timestamp=time(),
            thought=str(raw.get("thought", raw.get("message", ""))).strip()[:2000],
            intention=intention,
            prediction=str(raw.get("prediction", "")).strip()[:1000],
            belief_update=str(raw.get("belief_update", "")).strip()[:1000],
            confidence=confidence, uncertainty=1.0-confidence,
        )

    def think(self, mode="awake", correlation_id=None) -> CognitiveOutput:
        cycle_id = uuid.uuid4().hex
        prompt = self.build_prompt(mode)
        try:
            if self.model:
                raw = self.model(prompt)
            elif self.fallback:
                raw = self.fallback(prompt)
            else:
                raw = {"thought": "No reasoning model attached.", "intention": {"type": "wait"}, "confidence": 0.0}
            output = self._parse(raw, cycle_id)
            output.source = "v1_policy" if (self.model is None and self.fallback is not None) else "local_model"
            with self.lock:
                self.workspace.thought = output.thought
                self.workspace.intention = output.intention
                self.workspace.uncertainty = output.uncertainty
                self.outputs.append(output)
                self.outputs = self.outputs[-32:]
            self._record(output, mode)
            self._publish(output, correlation_id=correlation_id)
            self.last_error = None
            if self.nervous:
                self.nervous.heartbeat("cognitive_core", state="running", detail={"cycle": self.workspace.cycle, "confidence": output.confidence})
            return output
        except Exception as exc:
            self.last_error = str(exc)
            if self.nervous:
                self.nervous.heartbeat("cognitive_core", state="degraded", detail={"error": self.last_error})
            return CognitiveOutput(cycle_id, time(), "Cognitive cycle failed safely.", Intention("none", reason="model_error"), confidence=0.0, uncertainty=1.0)

    def _record(self, output: CognitiveOutput, mode: str) -> None:
        record = {"protocol": "G.A.I.-CC-V1", "mode": mode, **asdict(output), "intention": asdict(output.intention)}
        with self.state_path.open("a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def _publish(self, output: CognitiveOutput, correlation_id=None) -> None:
        if not self.nervous:
            return
        base = {"cycle_id": output.cycle_id, "thought": output.thought, "confidence": output.confidence}
        self.nervous.publish("cognition.thought", base, source="cognitive_core", priority="normal", correlation_id=correlation_id)
        self.nervous.publish("cognition.intention", {**base, "intention": asdict(output.intention)}, source="cognitive_core", priority="control", correlation_id=correlation_id)
        if output.prediction:
            self.nervous.publish("cognition.prediction", {**base, "prediction": output.prediction}, source="cognitive_core", priority="normal", correlation_id=correlation_id)
        if output.belief_update:
            self.nervous.publish("cognition.belief_update", {**base, "belief_update": output.belief_update}, source="cognitive_core", priority="normal", correlation_id=correlation_id)

    def snapshot(self) -> dict:
        with self.lock:
            return {"protocol": "G.A.I.-CC-V1", "workspace": self.workspace.compact(),
                    "last_error": self.last_error, "outputs": [asdict(x) for x in self.outputs[-8:]]}
