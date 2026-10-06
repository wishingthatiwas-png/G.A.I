from __future__ import annotations
import hashlib
import json
import multiprocessing as mp
import os
import socket
import subprocess
import threading
import time
import urllib.request
import uuid
from pathlib import Path

try:
    from perception.output_audio import emit_affect
    from perception.screen import snapshot as screen_snapshot
    from perception.input_audio import AudioInputOrgan
except ModuleNotFoundError:
    from agent.perception.output_audio import emit_affect
    from agent.perception.screen import snapshot as screen_snapshot
    from agent.perception.input_audio import AudioInputOrgan

ROOT = Path("/mnt/gai")
try:
    from core.scaling import character_budget, worker_ceiling, effective_metabolic_hz, compute_scale
except ModuleNotFoundError:
    from agent.core.scaling import character_budget, worker_ceiling


def _metabolic_worker():
    # Metabolism shares the same compute scale + simulation clock as the CNS.
    # It performs bounded work, then yields; it must not pin a CPU core forever.
    x = b"G.A.I."
    cfg_path = ROOT / "config/agent.json"
    speed_path = ROOT / "state/simulation_speed.json"
    while True:
        try:
            config = json.loads(cfg_path.read_text())
            speed_obj = json.loads(speed_path.read_text())
            hz = max(0.05, effective_metabolic_hz(config, speed_obj.get("multiplier", 1.0)))
            scale = compute_scale(config)
        except Exception:
            hz, scale = 0.2, 1.0
        rounds = max(2500, min(25000, int(5000 * min(scale, 5.0))))
        for _ in range(rounds):
            x = hashlib.sha256(x).digest()
        time.sleep(max(0.01, 1.0 / hz))


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
        try:
            cfg = json.loads((ROOT / "config/agent.json").read_text())
            self.central_cognition_v1 = bool(cfg.get("central_cognition_v1", False))
        except Exception:
            self.central_cognition_v1 = False
        self.audio_input = AudioInputOrgan(self.nervous)
        self.audio_input.start()

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
            ("cognition.intention", self.on_cognitive_intention, "agent.cognition.intention"),
        ]:
            self.nervous.subscribe(
                pattern, handler, name=name, component="agent"
            )

        self.socket_path = Path("/run/user/1000/gai-agent.sock")
        threading.Thread(target=self._serve, daemon=True, name="gai-agent-socket").start()
        if not self.central_cognition_v1:
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
        return max(1, min(int(round(requested)), worker_ceiling()))

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
            "audio_input": self._audio_input_state(),
            "cognitive_core": k.cognitive_core.snapshot() if hasattr(k, "cognitive_core") else {},
            "working_memory": k.working_memory.snapshot() if hasattr(k, "working_memory") else {},
        }

    def _audio_input_state(self):
        try:
            return json.loads((ROOT / "state/audio_input.json").read_text())
        except Exception:
            return {"available": False}

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
                if not self.central_cognition_v1:
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
        tasks = [
            {"action":"create_text", "task":"Write a short reflection about your current internal state and what you predict will happen next."},
            {"action":"create_image", "task":"Make a small abstract image representing your current internal state."},
            {"action":"paint", "task":"Make a simple abstract painting from your current mood and curiosity."},
            {"action":"save_observation", "task":"Inspect your actual available perception and save the observation."},
            {"action":"look", "task":"Look through your visual field at the current desktop and use that view to decide what you notice."},
            {"action":"output", "task":"Choose one of your output windows and arrange or reveal it so your current thought or work is visible."}
        ]
        task = tasks[len(self.history) % len(tasks)]
        prompt = {
            "mode": mode,
            "assigned_safe_task": task,
            "instruction": (
                "Exist independently. This is an internal cognitive cycle, not a user conversation. "
                "Generate one genuine internal thought based on your current state, recent perceptions, "
                "drives, predictions and memories. Then propose at most one safe intention. "
                "Do not pretend to have senses you do not have. Do not wait for a user. "
                "When there is no urgent body need, choose a safe activity: reflect, look through your visual field, write a short text artifact, make an SVG image, or make a simple SVG painting. "
                "Creative output should be about something you actually observed, predicted, remembered, or wondered about."
            ),
            "state": state,
        }
        decision = self._model(prompt, max_tokens=96)
        result = self.execute(decision)
        thought = str(decision.get("message", "")).strip()
        prior = [str(x.get("thought", "")).strip().lower() for x in self.history[-8:] if isinstance(x, dict)]
        words = set(w for w in thought.lower().split() if len(w) > 3)
        novelty = 1.0 if words and not any(len(words & set(p.split())) / max(1, len(words)) > .55 for p in prior) else 0.0
        completion = 0.25 if result.get("executed") and result.get("action") in {"create_text", "create_image", "paint"} else 0.0
        thinking_credit = min(0.5, 0.15 * novelty + completion)
        if thinking_credit:
            k.latest_reward = thinking_credit
            self.nervous.publish("reward.signal", {"value": thinking_credit, "kind": "thinking_credit", "novelty": novelty, "creative_completion": completion}, source="agent", priority="control")
        record = {
            "id": uuid.uuid4().hex,
            "timestamp": time.time(),
            "mode": mode,
            "thought": decision.get("message", ""),
            "action": result.get("action", "none"),
            "executed": result.get("executed", False),
        }
        raw_emotion = max(vars(k.motivation.emotions), key=vars(k.motivation.emotions).get)
        emotion = {
            "joy": "happiness",
            "pleasure": "happiness",
            "fear": "fear",
            "anxiety": "stress",
            "frustration": "stress",
            "contentment": "contentment",
            "fatigue": "fatigue",
            "sadness": "boredom",
            "loneliness": "boredom",
        }.get(raw_emotion, raw_emotion)
        self._publish_body_output(record["thought"], record["action"])
        try:
            audio_result = emit_affect(emotion, record["action"])
            self.nervous.publish("audio.output", audio_result, source="audio.organ", priority="normal")
        except Exception as exc:
            self.nervous.publish("agent.audio.error", {"error": str(exc)}, source="agent", priority="background")
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
            "Return JSON only: {message, action, target}. Do not produce hidden reasoning or a thinking trace. "
            "Allowed actions: none, observe, maintain, rest, save_observation, look, output, create_text, create_image, paint, face, move. "
            "Creative actions are safe and sandboxed under /mnt/gai/creative. They may create text or SVG artwork only. "
            "Thinking earns credit when it is novel, useful, or leads to a safe completed creative artifact; never invent reward."
        )
        context_text = json.dumps(context, separators=(",", ":"), default=str)
        budget = character_budget(self._metabolic_target())
        if len(context_text) > budget:
            context_text = context_text[:budget]
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": context_text},
            ],
            "temperature": 0.7,
            "stream": False,
            "max_tokens": max_tokens,
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
            try:
                (ROOT / "state/model_error.log").write_text(f"{time.time()} {type(e).__name__}: {e}\\n")
            except Exception:
                pass
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
        if a not in {"none", "observe", "maintain", "rest", "save_observation", "look", "output", "create_text", "create_image", "paint", "face", "move"}:
            a = "none"
        if a == "look":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            try:
                gx=max(0.0,min(1.0,float(target.get("x",0.5))))
                gy=max(0.0,min(1.0,float(target.get("y",0.5))))
            except (TypeError,ValueError):
                gx,gy=0.5,0.5
            gaze={"timestamp":time.time(),"x":gx,"y":gy,"target":target.get("target","desktop"),"reason":d.get("message","")}
            (ROOT/"state/gaze.json").write_text(json.dumps(gaze,separators=(",",":")))
            observation=screen_snapshot()
            (ROOT/"state/visual_perception.json").write_text(json.dumps(observation,default=str,separators=(",",":")))
            self.nervous.publish("perception.visual", observation, source="agent", priority="normal")
            return {"message":d.get("message",""),"action":a,"executed":bool(observation.get("captured")),"observation":observation,"agent_confirmed":True}
        if a == "output":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            allowed = {"view", "thought", "state", "text", "pixels"}
            operation = str(target.get("operation", "update"))
            if operation == "launch":
                pidfile = ROOT/"state/output_windows.pid"
                alive = False
                try:
                    pid = int(pidfile.read_text().strip()); os.kill(pid, 0); alive = True
                except Exception: pass
                if not alive:
                    env=dict(os.environ); env.setdefault("DISPLAY",":0"); env.setdefault("XAUTHORITY","/home/null/.Xauthority")
                    subprocess.Popen([str(ROOT/"venvs/gai/bin/python"),str(ROOT/"agent/gui/toy_app.py")], env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                return {"message":d.get("message",""),"action":a,"executed":True,"operation":"launch","already_running":alive,"agent_confirmed":True}
            windows = target.get("windows", [target.get("window")] if target.get("window") else [])
            if isinstance(windows, str): windows = [windows]
            windows = [w for w in windows if w in allowed]
            path = ROOT / "state/output_windows.json"
            try: current = json.loads(path.read_text())
            except Exception: current = {}
            for w in windows:
                w = "state" if w == "thought" else w
                spec = dict(current.get(w, {}))
                for key in ("visible","x","y","opacity","font_size"):
                    if key in target: spec[key] = target[key]
                current[w] = spec
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(current, indent=2))
            self.nervous.publish("ui.output", {"windows":windows,"target":target}, source="agent", priority="normal")
            return {"message":d.get("message",""),"action":a,"executed":bool(windows),"windows":windows,"agent_confirmed":True}
        if a == "move":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            try:
                dx = max(-500, min(500, float(target.get("dx", 0))))
                dy = max(-300, min(300, float(target.get("dy", 0))))
                duration = max(0.2, min(8.0, float(target.get("duration", 2.0))))
            except (TypeError, ValueError):
                dx, dy, duration = 0.0, 0.0, 2.0
            motor = {"timestamp": time.time(), "action": "move", "dx": dx, "dy": dy, "duration": duration, "reason": d.get("message", "")}
            path = ROOT / "state/motor_output.json"
            path.write_text(json.dumps(motor, separators=(",", ":")))
            self.nervous.publish("motor.output", motor, source="agent", priority="normal")
            return {"message": d.get("message", ""), "action": a, "executed": True, "motor": motor, "agent_confirmed": True}
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
        if a == "create_text":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            path = k.actions.create_text(target.get("title", "thought"), target.get("text", d.get("message", "")))
            return {"message": d.get("message", ""), "action": a, "executed": True, "artifact": path, "reward_basis": "creative_completion", "agent_confirmed": True}
        if a == "create_image":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            path = k.actions.create_image(target.get("title", "image"), target.get("text", d.get("message", "")))
            return {"message": d.get("message", ""), "action": a, "executed": True, "artifact": path, "reward_basis": "creative_completion", "agent_confirmed": True}
        if a == "paint":
            target = d.get("target") if isinstance(d.get("target"), dict) else {}
            path = k.actions.paint(target.get("title", "painting"), target.get("strokes", []))
            return {"message": d.get("message", ""), "action": a, "executed": True, "artifact": path, "reward_basis": "creative_completion", "agent_confirmed": True}
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

    def on_cognitive_intention(self, event):
        """Observe CC proposals only; the motor/action centre owns execution."""
        p = dict(event.payload or {})
        intention = p.get("intention") if isinstance(p.get("intention"), dict) else {}
        self.nervous.heartbeat("agent", detail={
            "last": event.kind,
            "proposal": str(intention.get("type", "none")),
            "executed": False,
            "execution_owner": "motor_action",
        })
    def on_event(self, event):
        self.nervous.heartbeat("agent", detail={"last": event.kind})
