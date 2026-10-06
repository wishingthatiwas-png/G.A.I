from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
ENVIRONMENT = STATE / "v1_environment.json"
SKIN = STATE / "digital_skin.json"


@dataclass
class CNSState:
    """Tiny homeostatic state used by V1. It is deliberately finite and inspectable."""
    energy: float = 0.75
    curiosity: float = 0.70
    stress: float = 0.10
    satisfaction: float = 0.50
    boredom: float = 0.15
    confidence: float = 0.50

    def clamp(self) -> None:
        for key in ("energy", "curiosity", "stress", "satisfaction", "boredom", "confidence"):
            setattr(self, key, max(0.0, min(1.0, float(getattr(self, key)))))

    def sync(self, state) -> None:
        self.energy = float(getattr(state, "energy", self.energy))
        self.curiosity = float(getattr(state, "curiosity", self.curiosity))
        self.stress = float(getattr(state, "stress", self.stress))
        self.satisfaction = float(getattr(state, "satisfaction", self.satisfaction))
        self.boredom = float(getattr(state, "boredom", self.boredom))
        self.confidence = float(getattr(state, "confidence", self.confidence))
        self.clamp()

    def apply_reward(self, reward: float, prediction_error: float = 0.0) -> None:
        reward = max(-1.0, min(1.0, float(reward)))
        surprise = max(0.0, min(1.0, float(prediction_error)))
        self.satisfaction = max(0.0, min(1.0, self.satisfaction + reward * 0.10))
        self.curiosity = max(0.0, min(1.0, self.curiosity + surprise * 0.05 - reward * 0.02))
        self.stress = max(0.0, min(1.0, self.stress - reward * 0.05 + surprise * 0.02))
        self.boredom = max(0.0, min(1.0, self.boredom + 0.03 - self.curiosity * 0.02))
        self.clamp()

    def snapshot(self) -> dict:
        return asdict(self)


class V1World:
    """One safe, persistent object for the baby to investigate."""

    def __init__(self, path: Path = ENVIRONMENT):
        self.path = path
        self.state = self._load()

    def _load(self) -> dict:
        try:
            obj = json.loads(self.path.read_text())
            if isinstance(obj, dict) and "object" in obj:
                return obj
        except Exception:
            pass
        obj = {
            "version": 1,
            "object": {
                "id": "curiosity_object",
                "x": 0.68,
                "y": 0.50,
                "state": "quiet",
                "changes": 0,
            },
            "last_action": None,
            "last_outcome": None,
            "last_reward": 0.0,
            "timestamp": time.time(),
        }
        self.save(obj)
        return obj

    def save(self, obj=None) -> None:
        if obj is not None:
            self.state = obj
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=2))

    def target_px(self, screen_w: float, screen_h: float) -> tuple[float, float]:
        obj = self.state["object"]
        return float(obj["x"]) * screen_w, float(obj["y"]) * screen_h

    def observe(self) -> dict:
        obj = self.state["object"]
        return {
            "id": obj["id"],
            "x": obj["x"],
            "y": obj["y"],
            "state": obj["state"],
            "changes": obj["changes"],
            "last_outcome": self.state.get("last_outcome"),
            "last_reward": self.state.get("last_reward", 0.0),
        }

    def interact(self, *, distance: float, threshold: float = 120.0) -> dict:
        now = time.time()
        if distance <= threshold:
            obj = self.state["object"]
            obj["state"] = "active" if obj["state"] != "active" else "quiet"
            obj["changes"] = int(obj.get("changes", 0)) + 1
            outcome = {
                "success": True,
                "object": obj["id"],
                "new_state": obj["state"],
                "changes": obj["changes"],
                "distance": round(distance, 1),
            }
            reward = 1.0
        else:
            outcome = {
                "success": False,
                "object": self.state["object"]["id"],
                "new_state": self.state["object"]["state"],
                "changes": self.state["object"].get("changes", 0),
                "distance": round(distance, 1),
            }
            reward = -0.15
        self.state["last_outcome"] = outcome
        self.state["last_reward"] = reward
        self.state["last_action"] = "interact"
        self.state["timestamp"] = now
        self.save()
        SKIN.parent.mkdir(parents=True, exist_ok=True)
        SKIN.write_text(json.dumps({
            "timestamp": now,
            "channel": "contact",
            "contact": bool(outcome["success"]),
            "object": outcome["object"],
            "distance_px": round(distance, 1),
            "intensity": 1.0 if outcome["success"] else 0.0,
            "outcome": outcome,
        }, separators=(",", ":")))
        return {"reward": reward, "outcome": outcome}


class SharedAttention:
    """Cross-modal salience gate with motion, transients, synchrony and habituation."""

    def __init__(self, path: Path = STATE / "attention.json"):
        self.path = path
        self.last = {}

    def select(self, senses: dict, world: dict, drives: dict) -> dict:
        candidates = []
        vision = senses.get("vision") or {}
        audio = senses.get("audio") or {}
        temporal = vision.get("temporal") or {}
        auditory = audio.get("auditory") or {}

        motion_salience = float(temporal.get("salience", 0.0) or 0.0)
        onset = float(temporal.get("onset", 0.0) or 0.0)
        velocity = float(temporal.get("velocity", 0.0) or 0.0)
        sensory_novelty = float(vision.get("sensory_novelty", 0.0) or 0.0)

        visual_novelty_salience = min(
            1.0,
            0.45 * sensory_novelty + 0.35 * motion_salience + 0.20 * onset,
        )
        if visual_novelty_salience > 0.06:
            candidates.append({
                "modality": "vision",
                "target": "visual_event",
                "salience": visual_novelty_salience,
                "reason": "visual_novelty",
            })

        if motion_salience > 0.02:
            candidates.append({
                "modality": "vision",
                "target": "moving_region",
                "salience": min(1.0, motion_salience),
                "reason": "motion",
                "direction": temporal.get("direction", "still"),
                "onset": round(onset, 4),
                "velocity": round(velocity, 4),
            })

        signal = float(audio.get("signal", 0.0) or 0.0)
        transient = min(1.0, float(auditory.get("transient", 0.0) or 0.0) * 15.0)
        audio_novelty = 1.0 if transient > 0.40 else 0.0
        # Steady audio is modest; a genuinely strong sound can still capture attention.
        audio_salience = min(1.0, 0.50 * signal + 0.38 * transient + 0.12 * audio_novelty)
        if bool(audio.get("fresh")) and audio_salience > 0.08:
            candidates.append({
                "modality": "audio",
                "target": "sound",
                "salience": audio_salience,
                "reason": "auditory_signal",
                "transient": round(transient, 4),
            })

        synchrony = min(motion_salience, transient)
        if synchrony > 0.025:
            candidates.append({
                "modality": "multimodal",
                "target": "audiovisual_event",
                "salience": min(1.0, 0.45 * motion_salience + 0.30 * transient + 0.35 * synchrony),
                "reason": "audiovisual_synchrony",
            })

        concepts = vision.get("concepts") or []
        patterns = vision.get("patterns") or []
        pattern_affect = {str(p.get("emotion", "neutral")) for p in patterns[:4]}
        affect_boost = 0.04 if pattern_affect & {"curiosity", "wonder", "warmth", "interesting"} else 0.0
        caution_penalty = 0.04 if pattern_affect & {"caution", "uncertain"} else 0.0
        for concept in concepts[:4]:
            candidates.append({
                "modality": "vision",
                "target": str(concept),
                "salience": max(0.08, min(0.45, 0.16 + affect_boost - caution_penalty)),
                "reason": "visual_concept",
            })

        obj = world.get("object") or {}
        world_salience = 0.18 + 0.15 * float(drives.get("curiosity", 0.0))
        if obj.get("state") == "active":
            world_salience += 0.10
        candidates.append({
            "modality": "world",
            "target": obj.get("id", "curiosity_object"),
            "salience": min(0.70, world_salience),
            "reason": "internal_target",
        })

        candidates.sort(key=lambda item: (-item["salience"], item["modality"], str(item["target"])))
        selected = candidates[0] if candidates else {
            "modality": "none", "target": None, "salience": 0.0, "reason": "nothing_salient"
        }
        result = {
            "selected": selected,
            "candidates": candidates[:8],
            "timestamp": time.time(),
            "curiosity": float(drives.get("curiosity", 0.0)),
            "salience_field": {
                "motion": round(motion_salience, 4),
                "audio": round(audio_salience, 4),
                "audiovisual_synchrony": round(synchrony, 4),
                "sensory_novelty": round(sensory_novelty, 4),
            },
        }
        self.last = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(result, separators=(",", ":"), default=str))
        return result


class BabyBrain:
    """Simple, model-free CNS + CC for V1.

    It chooses from a tiny action set using needs, novelty, learned effects and
    bounded exploration. The language model can be plugged in later without
    changing the body/action contract.
    """

    ACTIONS = ("rest", "look", "move", "interact", "vocalize", "wait")

    def __init__(self, kernel):
        self.kernel = kernel
        self.cns = CNSState()
        self.world = V1World()
        self.attention = SharedAttention()
        self.cycle = 0
        self.last_decision: dict = {}
        self.last_reward = 0.0
        self.last_prediction_error = 0.0
        self.rng = random.Random()

    @staticmethod
    def _screen_size(kernel) -> tuple[float, float]:
        prop = {}
        try:
            prop = json.loads((STATE / "proprioception.json").read_text())
        except Exception:
            pass
        return (
            float(prop.get("screen_width", prop.get("screen_center_x", 1920))),
            float(prop.get("screen_height", prop.get("screen_center_y", 1080))),
        )

    @staticmethod
    def _distance(kernel, tx: float, ty: float) -> float:
        try:
            prop = json.loads((STATE / "proprioception.json").read_text())
            x = float(prop.get("x", prop.get("screen_center_x", tx)))
            y = float(prop.get("y", prop.get("screen_center_y", ty)))
            return ((tx - x) ** 2 + (ty - y) ** 2) ** 0.5
        except Exception:
            return 9999.0

    def _novelty(self) -> float:
        senses = self.kernel.last_senses or {}
        vision = senses.get("vision") or {}
        temporal = vision.get("temporal") or {}
        sensory_novelty = float(vision.get("sensory_novelty", 0.0) or 0.0)
        salience = float(temporal.get("salience", 0.0) or 0.0)
        structural = float(self.kernel.perception_novelty())
        return max(
            0.0,
            min(1.0, 0.55 * sensory_novelty + 0.30 * salience + 0.15 * structural),
        )

    def _observe_previous_outcome(self) -> None:
        """Apply the consequence of the previous selected action exactly once."""
        learner = self.kernel.learner
        previous_action = (
            self.last_decision.get("intention", {}).get("type")
            if self.last_decision else None
        )
        self.last_prediction_error = float(getattr(learner, "last_error", 0.0) or 0.0)

        if previous_action == "interact":
            self.last_reward = max(-1.0, min(1.0, float(self.world.state.get("last_reward", 0.0))))
        elif previous_action is None:
            self.last_reward = 0.0
            self.last_prediction_error = 0.0
        else:
            delta = getattr(learner, "last_delta", {}) or {}
            reward = (
                0.80 * float(delta.get("curiosity", 0.0))
                + 1.00 * float(delta.get("satisfaction", 0.0))
                - 1.20 * float(delta.get("safety", 0.0))
                - 1.00 * float(delta.get("energy", 0.0))
            )
            self.last_reward = max(-1.0, min(1.0, reward))

        self.kernel.latest_reward = self.last_reward
        self.kernel.latest_prediction_error = self.last_prediction_error
        self.cns.apply_reward(self.last_reward, self.last_prediction_error)

    def _experience_context(self, attention: dict, novelty: float) -> list[str]:
        senses = self.kernel.last_senses or {}
        vision = senses.get("vision") or {}
        patterns = vision.get("patterns") or []
        selected = attention.get("selected", {})
        temporal = (vision.get("temporal") or {})
        labels = [
            f"attention:{selected.get('modality')}:{selected.get('target')}",
            f"attention_band:{'high' if float(selected.get('salience', 0.0)) > .55 else 'low'}",
            f"world:{self.world.state.get('object', {}).get('state', 'quiet')}",
            f"novelty:{'high' if novelty > .55 else 'low'}",
            f"boredom:{'high' if self.cns.boredom > .55 else 'low'}",
            f"motion:{temporal.get('direction', 'still')}",
        ]
        for pattern in patterns[:2]:
            labels.append(f"pattern:{pattern.get('colour','gray')}:{pattern.get('shape','polygon')}")
        return labels

    def _memory_bias(self, action: str) -> float:
        """Small recall-derived bias; memory informs CC but never becomes a controller."""
        hits = getattr(self, "memory_hits", []) or []
        if not hits:
            return 0.0
        value = 0.0
        for hit in hits[:5]:
            data = hit.get("data", {}) or {}
            focus = str(data.get("focus", ""))
            words = {str(w).lower() for w in data.get("words", [])}
            if focus == action:
                value += 0.12 * float(hit.get("relevance", 0.0))
            if action in words:
                value += 0.05 * float(hit.get("relevance", 0.0))
            outcome = data.get("outcome", {}) or {}
            if outcome.get("success") is True and focus == action:
                value += 0.08 * float(hit.get("relevance", 0.0))
        return min(0.25, value)

    def _score(self, action: str, *, novelty: float, distance: float, learned: dict) -> float:
        fatigue = float(self.kernel.state.fatigue)
        stress = float(self.kernel.state.stress)
        curiosity = float(self.kernel.state.curiosity)
        boredom = float(self.kernel.state.boredom)

        score = 0.0
        motivation = getattr(self.kernel, "motivation", None)
        need_bonus = float(motivation.score_action("rest")) if motivation is not None and action == "rest" else 0.0
        if motivation is not None and action in {"interact", "vocalize"}:
            need_bonus += 0.65 * float(motivation.score_action("interact"))
        if motivation is not None and action in {"move", "look"}:
            need_bonus += 0.55 * float(motivation.score_action("explore"))
        if action == "rest":
            rest_debt = float(getattr(getattr(self.kernel, "core_needs", None), "rest", 0.0))
            score = 0.35 * fatigue + 0.25 * stress + 0.35 * rest_debt - 0.70 * curiosity - 0.35 * boredom
        elif action == "look":
            score = 0.70 * novelty + 0.65 * curiosity + 0.20 * boredom - 0.20 * stress
        elif action == "move":
            score = 1.00 * curiosity + 0.70 * novelty + 0.60 * boredom - 0.30 * stress - 0.45 * fatigue
            score += min(0.7, distance / 700.0)
        elif action == "interact":
            proximity = max(0.0, 1.0 - distance / 220.0)
            score = 1.30 * curiosity + 1.00 * novelty + 1.50 * proximity + 0.70 * boredom - 0.25 * stress - 0.35 * fatigue
        elif action == "vocalize":
            # Vocal play is a safe, cheap social/curiosity outlet.
            score = 0.55 * curiosity + 0.45 * novelty + 0.75 * boredom + 0.25 * (1.0 - stress)
        elif action == "wait":
            score = 0.05 + 0.15 * stress + 0.10 * fatigue - 0.50 * curiosity - 0.90 * boredom

        # Needs bias action selection without becoming a second controller.
        score += need_bonus
        score += self._memory_bias(action)
        # Learned predicted change is deliberately a small term, not the whole brain.
        if learned:
            score += 0.80 * float(learned.get("satisfaction", 0.0))
            score -= 0.45 * float(learned.get("safety", 0.0))
        return score

    def _sample_experience(self, actions, scores, context, temperature):
        policy = getattr(self.kernel, "experience_policy", None)
        if policy is not None:
            return policy.sample(actions, scores, context, temperature=temperature)
        chosen = max(actions, key=lambda action: scores[action])
        return chosen, dict(scores), {action: 0.0 for action in actions}

    def decide(self) -> dict:
        _decision_start = time.perf_counter()
        self._observe_previous_outcome()
        self.cns.sync(self.kernel.state)
        self.cycle += 1
        user_request = getattr(self.kernel, "user_action_request", None)
        if isinstance(user_request, dict) and user_request.get("command") == "move":
            # An accepted user request enters the normal CNS/CC intention path.
            # The command layer has already asked whether G.A.I. agrees; motor
            # execution still happens through the ordinary action centre.
            self.kernel.user_action_request = None
            decision = {
                "thought": "I agreed to move, so I will try it.",
                "intention": {
                    "type": "move",
                    "target": {"object": "curiosity_object", "dx": 80.0, "dy": 0.0, "duration": 0.65},
                    "priority": 0.75,
                    "reason": str(user_request.get("reason", "accepted user request")),
                },
                "prediction": {"action": "move", "expected_effect": "change position"},
                "confidence": 0.80,
                "cycle": self.cycle,
                "scores": {"user_request_move": 1.0},
                "base_scores": {"user_request_move": 1.0},
                "experience_context": ["user_request:move", "agreed:true"],
                "attention": self.attention.last or {},
                "decision_ms": 0.0,
            }
            self.kernel.learner.choose("move", decision["experience_context"], self.kernel.drive_values())
            self.last_decision = decision
            return decision
        sw, sh = self._screen_size(self.kernel)
        tx, ty = self.world.target_px(sw, sh)
        distance = self._distance(self.kernel, tx, ty)
        novelty = self._novelty()
        drives = self.kernel.drive_values()
        
        neural = getattr(self.kernel, "neural_fabric", None)
        attention = getattr(self.kernel, "neural_attention", None)
        if attention is None and neural is not None:
            attention = neural.select_attention(self.kernel.last_senses)
        if attention is None:
            attention = self.attention.select(self.kernel.last_senses, self.world.state, drives)
        selected_attention = attention["selected"]
        if hasattr(self.kernel, "nervous"):
            self.kernel.nervous.publish(
                "attention.selected",
                attention,
                source="v1_attention",
                priority="control",
                correlation_id=getattr(self.kernel, "current_correlation", None),
            )
        context = self.kernel.current_context() + [
            "v1", self.world.state["object"]["state"],
            f"attention:{selected_attention['modality']}:{selected_attention['target']}",
        ]
        predictions = {a: self.kernel.learner.predict(a, context) for a in self.ACTIONS}
        scores = {a: self._score(a, novelty=novelty, distance=distance, learned=predictions[a]) for a in self.ACTIONS}
        experience_context = self._experience_context(attention, novelty)
        memory_api = getattr(self.kernel, "memory", None)
        self.memory_hits = memory_api.recall_relevant(
            experience_context + [str(self.world.state["object"]["id"]), str(selected_attention.get("target"))],
            limit=5,
        ) if memory_api is not None and hasattr(memory_api, "recall_relevant") else []
        for hit in self.memory_hits[:3]:
            experience_context.append(f"memory:{hit.get('tier')}:{hit.get('kind')}:{float(hit.get('relevance',0.0)):.2f}")
        if self.memory_hits and memory_api is not None and hasattr(memory_api, "reinforce_relevant"):
            memory_api.reinforce_relevant(experience_context, limit=2, boost=0.02)
        scores = {a: self._score(a, novelty=novelty, distance=distance, learned=predictions[a]) for a in self.ACTIONS}
        chosen, combined_scores, learned_preferences = self._sample_experience(
            self.ACTIONS, scores, experience_context,
            temperature=max(0.28, 0.70 - 0.30 * self.cns.confidence),
        )
        score = combined_scores[chosen]

        if chosen == "move":
            dx = max(-220.0, min(220.0, tx - (sw / 2 if distance >= 9000 else tx - (tx - distance))))
            try:
                prop = json.loads((STATE / "proprioception.json").read_text())
                px, py = float(prop.get("x", sw / 2)), float(prop.get("y", sh / 2))
            except Exception:
                px, py = sw / 2, sh / 2
            dx = max(-180.0, min(180.0, tx - px))
            dy = max(-120.0, min(120.0, ty - py))
            target = {"object": "curiosity_object", "dx": dx, "dy": dy, "duration": 0.65}
        elif chosen == "look":
            target = {"x": self.world.state["object"]["x"], "y": self.world.state["object"]["y"], "target": "camera", "mode": "out"}
        elif chosen == "interact":
            target = {"object": "curiosity_object"}
        elif chosen == "vocalize":
            target = {"kind": "tone"}
        else:
            target = {}

        thoughts = {
            "rest": "I can rest when I need to.",
            "look": "Something may be worth attending to.",
            "move": "I want to get closer to the interesting thing.",
            "interact": "I am close enough to find out what it does.",
            "vocalize": "vocal impulse",
            "wait": "Nothing demands action right now.",
        }
        decision = {
            "thought": thoughts[chosen],
            "intention": {
                "type": chosen,
                "target": target,
                "priority": max(0.0, min(1.0, 0.55 + score * 0.08)),
                "reason": (
                    f"attention={selected_attention['modality']}:{selected_attention['target']} "
                    f"curiosity={self.cns.curiosity:.2f} novelty={novelty:.2f} distance={distance:.0f}"
                ),
            },
            "prediction": {
                "action": chosen,
                "object": self.world.state["object"]["id"],
                "distance": round(distance, 1),
                "expected_effect": predictions[chosen],
            },
            "confidence": max(0.1, min(0.95, 0.45 + abs(score) * 0.08)),
            "cycle": self.cycle,
            "scores": {k: round(v, 4) for k, v in combined_scores.items()},
            "base_scores": {k: round(v, 4) for k, v in scores.items()},
            "experience_context": experience_context,
            "attention": attention,
            "decision_ms": round((time.perf_counter() - _decision_start) * 1000.0, 1),
        }
        self.kernel.learner.choose(chosen, context, self.kernel.drive_values())
        self.last_decision = decision
        return decision

    def record_outcome(self, action_result: dict | None = None) -> None:
        action_result = action_result or {}
        action = self.last_decision.get("intention", {}).get("type", "none")
        ctx = self.last_decision.get("experience_context", [])
        result = action_result if isinstance(action_result, dict) else {}
        outcome_reward = (
            0.65 if result.get("success") is True
            else -0.30 if result.get("success") is False
            else 0.10 if action not in {"wait", "rest"} else 0.0
        )
        # This reward belongs to the action that just happened. It must never be
        # confused with last_reward, which describes the previous action's
        # measured body-state consequence.
        self.kernel.experience_policy.observe(action, ctx, outcome_reward)
        trace = {
            "timestamp": time.time(),
            "cycle": self.cycle,
            "correlation_id": getattr(self.kernel, "current_correlation", None),
            "input": {
                # Trace the compressed sensory state, not raw audio spectra or
                # full camera payloads. Raw organs remain available to diagnostics.
                "vision": {
                    "temporal": (self.kernel.last_senses.get("vision") or {}).get("temporal", {}),
                    "patterns": (self.kernel.last_senses.get("vision") or {}).get("patterns", [])[:2],
                    "concepts": (self.kernel.last_senses.get("vision") or {}).get("concepts", [])[:12],
                    "novelty": (self.kernel.last_senses.get("vision") or {}).get("sensory_novelty", 0.0),
                    "habituation": (self.kernel.last_senses.get("vision") or {}).get("habituation", 0.0),
                },
                "audio": {
                    "signal": (self.kernel.last_senses.get("audio") or {}).get("signal", 0.0),
                    "rms": (self.kernel.last_senses.get("audio") or {}).get("rms", 0.0),
                    "transient": ((self.kernel.last_senses.get("audio") or {}).get("auditory") or {}).get("transient", 0.0),
                    "attended_frequency": ((self.kernel.last_senses.get("audio") or {}).get("auditory") or {}).get("attended_frequency", 0.0),
                },
                "context": self.kernel.current_context(),
                "novelty": self._novelty(),
            },
            "cns": self.cns.snapshot(),
            "thought": self.last_decision.get("thought", ""),
            "attention": self.last_decision.get("attention", {}).get("selected", {}),
            "action": action,
            "prediction": self.last_decision.get("prediction", {}),
            "decision_ms": self.last_decision.get("decision_ms", 0.0),
            "tick_timings_ms": getattr(self.kernel, "_last_tick_timings", {}),
            "outcome": result,
            "outcome_reward": outcome_reward,
            "previous_action_reward": self.last_reward,
            "prediction_error": self.last_prediction_error,
            "environment": self.world.observe(),
        }
        path = STATE / "v1_trace.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(trace, separators=(",", ":"), default=str) + "\n")

    def snapshot(self) -> dict:
        return {
            "cns": self.cns.snapshot(),
            "world": self.world.observe(),
            "cycle": self.cycle,
            "last_reward": self.last_reward,
            "last_prediction_error": self.last_prediction_error,
            "last_decision": self.last_decision,
            "attention": self.attention.last,
            "cns_input": {
                "energy": self.kernel.state.energy,
                "curiosity": self.kernel.state.curiosity,
                "boredom": self.kernel.state.boredom,
                "stress": self.kernel.state.stress,
                "satisfaction": self.kernel.state.satisfaction,
                "confidence": self.kernel.state.confidence,
            },
        }
