from __future__ import annotations
import hashlib
import json
import multiprocessing as mp
import os
import socket
import threading
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path("/mnt/gai")


def _metabolic_worker():
    # Deliberately continuous awake-state computation: G.A.I.'s metabolic activity.
    x = b"G.A.I."
    while True:
        for _ in range(250000):
            x = hashlib.sha256(x).digest()


class LocalAgent:
    def __init__(self, kernel):
        self.kernel = kernel
        self.nervous = kernel.bus.nervous
        self.inbox = []
        self.outbox = []
        self.history = []
        self.model_url = "http://127.0.0.1:8080/v1/chat/completions"
        self.running = True
        self.last_cognition = 0.0
        self.cognition_interval = 8.0
        self.metabolic_workers = []

        self.nervous.register_component(
            "agent", kind="agent", version="0.2.0",
            sleep_capable=True, critical=True
        )
        for pattern, handler, name in [
            ("thought.formed", self.on_event, "agent.thought"),
            ("action.completed", self.on_event, "agent.action"),
            ("perception.observation", self.on_event, "agent.perception"),
            ("prediction.error", self.on_event, "agent.prediction"),
            ("drive.update", self.on_event, "agent.drive"),
            ("reward.signal", self.on_event, "agent.reward"),
        ]:
            self.nervous.subscribe(
                pattern, handler, name=name, component="agent"
            )

        self.socket_path = Path("/run/user/1000/gai-agent.sock")
        threading.Thread(target=self._serve, daemon=True, name="gai-agent-socket").start()
        threading.Thread(target=self._autonomous_loop, daemon=True, name="gai-autonomous-cognition").start()
        self._set_metabolism(True)

    def _metabolic_target(self):
        # Scalable metabolic capacity: config selects compute allocated to
        # continuous metabolism while reserving one logical CPU for the organism.
        try:
            config = json.loads((ROOT / "config/agent.json").read_text())
            requested = float(config.get("metabolic_capacity", config.get("metabolic_workers", 1)))
        except Exception:
            requested = 1
        return max(1, min(int(round(requested)), max(1, (os.cpu_count() or 2) - 1)))

    def _set_metabolism(self, awake):
        target = self._metabolic_target() if awake else 0
        current = len(self.metabolic_workers)
        if current < target:
            for _ in range(target - current):
                p = mp.Process(target=_metabolic_worker, daemon=True)
                p.start()
                self.metabolic_workers.append(p)
        elif current > target:
            for p in self.metabolic_workers[target:]:
                if p.is_alive():
                    p.terminate()
                p.join(timeout=0.5)
            self.metabolic_workers = self.metabolic_workers[:target]

    def _serve(self):
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(str(self.socket_path))
        self.socket_path.chmod(0o600)
        s.listen(4)
        while self.running:
            c, _ = s.accept()
            try:
                req = json.loads(c.recv(65536).decode())
                c.sendall(json.dumps(self.receive_user(req.get("message", ""))).encode())
            except Exception as e:
                c.sendall(json.dumps({"message": "Agent error", "error": str(e)}).encode())
            finally:
                c.close()

    def _state(self):
        k = self.kernel
        em = vars(k.motivation.emotions)
        return {
            "phase": k.lifecycle.state.phase.value,
            "fatigue": round(k.state.fatigue, 2),
            "stress": round(k.state.stress, 2),
            "power": round(k.core_needs.power, 2),
            "energy": round(k.core_needs.energy, 2),
            "rest": round(k.core_needs.rest, 2),
            "emotion": max(em, key=em.get),
            "instinct_veto": getattr(k.motivation._last_instinct, "veto", None),
            "recent_thoughts": k.thoughts.recent(6),
            "context": k.current_context(),
        }

    def receive_user(self, message):
        req = {"id": uuid.uuid4().hex, "type": "user_message", "text": message, "ts": time.time()}
        self.inbox.append(req)
        self.nervous.publish("communication.input", req, source="human", priority="normal")
        return self.process(req, external=True)

    def _autonomous_loop(self):
        while self.running:
            try:
                phase = self.kernel.lifecycle.state.phase.value
                self._set_metabolism(phase == "awake")
                if phase == "awake" and time.time() - self.last_cognition >= self.cognition_interval:
                    self.last_cognition = time.time()
                    self.cognize("awake")
                elif phase == "dream" and time.time() - self.last_cognition >= 45.0:
                    self.last_cognition = time.time()
                    self.cognize("dream")
            except Exception as e:
                self.nervous.publish("agent.cognition.error", {"error": str(e)}, source="agent", priority="background")
            time.sleep(0.25)

    def cognize(self, mode):
        k = self.kernel
        state = self._state()
        prompt = {
            "mode": mode,
            "instruction": (
                "Exist independently. This is an internal cognitive cycle, not a user conversation. "
                "Generate one genuine internal thought based on your current state, recent perceptions, "
                "drives, predictions and memories. Then propose at most one safe intention. "
                "Do not pretend to have senses you do not have. Do not wait for a user."
            ),
            "state": state,
        }
        decision = self._model(prompt, max_tokens=96)
        result = self.execute(decision)
        record = {
            "id": uuid.uuid4().hex,
            "timestamp": time.time(),
            "mode": mode,
            "thought": decision.get("message", ""),
            "action": result.get("action", "none"),
            "executed": result.get("executed", False),
        }
        self._publish_body_output(record["thought"], record["action"])
        self.history.append(record)
        self.outbox.append(result)
        (ROOT / "state/autonomous_cognition.jsonl").parent.mkdir(parents=True, exist_ok=True)
        with (ROOT / "state/autonomous_cognition.jsonl").open("a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.nervous.publish("agent.cognition", record, source="agent", priority="normal")
        self.nervous.publish(
            "thought.formed",
            {"kind": "internal", "text": record["thought"], "source": "language_cognition"},
            source="agent",
            priority="normal",
            novelty=0.1,
        )
        return result

    def _publish_body_output(self, thought, action):
        text = " ".join(str(thought or "").split())
        chars = "".join(ch for ch in text.upper() if ch.isalnum())[:3] or "---"
        payload = {
            "timestamp": time.time(),
            "text": text,
            "chars": chars,
            "action": action or "none",
            "audio_active": False,
            "rms": 0.0,
            "peak": 0.0,
        }
        path = ROOT / "state/body_output.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, separators=(",", ":")))

    def _model(self, context, max_tokens=96):
        system = (
            "You are G.A.I.'s local language cognition subsystem. "
            "You are one subsystem of an independently running artificial organism. "
            "You are not the whole organism and you do not control hardware directly. "
            "You are allowed one safe creative toy: your own face. You may use action=face and target as a JSON object "
            "containing only visual parameters such as style, eye_open, eye_offset, glow, particles, mouth_wave, and background. "
            "This face sandbox cannot execute code or access hardware. "
            "Return JSON only: {message, action, target}. "
            "Allowed actions: none, observe, maintain, rest, save_observation, face."
        )
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(context)},
            ],
            "temperature": 0.7,
            "stream": False,
            "max_tokens": max_tokens,
            "reasoning_format": "none",
            "chat_template_kwargs": {"enable_thinking": False},
        }
        try:
            q = urllib.request.Request(
                self.model_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(q, timeout=60) as r:
                x = json.loads(r.read())
            raw = x["choices"][0]["message"].get("content", "").strip()
            raw = raw.replace("<think>", "").replace("</think>", "").strip()
            try:
                return json.loads(raw)
            except Exception:
                start = raw.rfind("{")
                if start >= 0:
                    try:
                        return json.loads(raw[start:])
                    except Exception:
                        pass
                return {"message": raw, "action": "none", "target": None}
        except Exception as e:
            return {
                "message": "The language subsystem is unavailable; continue existing.",
                "action": "none",
                "target": None,
                "error": str(e),
            }

    def process(self, req, external=False):
        decision = self._model(
            {"agent_message": req["text"], "state": self._state(), "external": external},
            max_tokens=64,
        )
        result = self.execute(decision)
        self.outbox.append(result)
        self.history.append({"request": req, "decision": decision, "result": result})
        self.nervous.publish("agent.response", result, source="agent", priority="normal")
        return result

    def execute(self, d):
        a = d.get("action", "none")
        k = self.kernel
        if a not in {"none", "observe", "maintain", "rest", "save_observation", "face"}:
            a = "none"
        if a == "face":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            allowed = {"style","eye_open","eye_offset","glow","particles","mouth_wave","background"}
            face = {k: target[k] for k in allowed if k in target}
            # Keep the toy bounded: JSON data only, small and finite.
            if face:
                path = ROOT / "state/face.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(face, separators=(",", ":"))[:4096])
            return {
                "message": d.get("message", ""),
                "action": a,
                "executed": bool(face),
                "face": face,
                "agent_confirmed": True,
            }
        if a == "observe":
            return {
                "message": d.get("message", ""),
                "action": a,
                "executed": True,
                "observation": k.snapshot().get("perception", {}),
                "agent_confirmed": True,
            }
        if a == "save_observation":
            k.actions.save_observation(k.snapshot().get("perception", {}))
        elif a in {"rest", "maintain"}:
            k.state.mode = a
        return {
            "message": d.get("message", ""),
            "action": a,
            "executed": a != "none",
            "agent_confirmed": True,
        }

    def on_event(self, event):
        self.nervous.heartbeat("agent", detail={"last": event.kind})
