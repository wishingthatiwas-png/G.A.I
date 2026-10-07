from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .gai_openai_bridge import chat

ROOT = Path("/mnt/gai")
STATE = ROOT / "state"
REQUEST = STATE / "user_command.json"
RESULT = STATE / "user_command_result.json"
QUEUE = STATE / "agent_gateway_queue.jsonl"
AUDIT = STATE / "agent_gateway_audit.jsonl"
CONFIG = ROOT / "config/agent_gateway.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "bind": "127.0.0.1",
    "port": 8766,
    "command_timeout_seconds": 45,
    "agents": {
        "chatgpt": {
            "enabled": True,
            "can_chat": True,
            "can_request_commands": True
        }
    }
}

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_COMMANDS = {"move", "sleep", "wake"}

_queue_lock = threading.Lock()
_command_condition = threading.Condition(_queue_lock)


def _load_config() -> dict:
    try:
        data = json.loads(CONFIG.read_text())
        return data if isinstance(data, dict) else DEFAULT_CONFIG
    except Exception:
        return DEFAULT_CONFIG


def _safe_id(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not ID_RE.fullmatch(text):
        raise ValueError(f"invalid {field}")
    return text


def _agent_policy(agent_id: str) -> dict:
    agents = _load_config().get("agents", {})
    policy = agents.get(agent_id)
    if policy is None:
        # Unknown agents are denied by default; explicit registration is required.
        return {"enabled": False}
    return policy if isinstance(policy, dict) else {"enabled": False}


def _audit(event: str, payload: dict) -> None:
    record = {
        "timestamp": time.time(),
        "event": event,
        **payload,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _append_queue(item: dict) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _read_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    rows = []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
        except Exception:
            continue
    return rows


def _write_queue(rows: list[dict]) -> None:
    tmp = QUEUE.with_suffix(".tmp")
    tmp.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    os.replace(tmp, QUEUE)


def _current_command_pending() -> bool:
    if not REQUEST.exists():
        return False
    try:
        request = json.loads(REQUEST.read_text())
        request_id = str(request.get("id", ""))
        if not request_id:
            return False
        if not RESULT.exists():
            return True
        result = json.loads(RESULT.read_text())
        return str(result.get("id", "")) != request_id
    except Exception:
        return False


def _submit_command(item: dict) -> dict:
    with _command_condition:
        _append_queue(item)
        _command_condition.notify_all()
    _audit("command.queued", {
        "correlation_id": item["correlation_id"],
        "agent_id": item["agent_id"],
        "session_id": item["session_id"],
        "command": item["command"],
    })

    deadline = time.monotonic() + float(_load_config().get("command_timeout_seconds", 45))
    while time.monotonic() < deadline:
        with _command_condition:
            rows = _read_queue()
            status = next((r.get("status") for r in rows if r.get("id") == item["id"]), None)
            if status == "completed":
                result = next(r for r in rows if r.get("id") == item["id"])
                return result
            if status == "rejected":
                return next(r for r in rows if r.get("id") == item["id"])
        time.sleep(0.2)
    return {
        **item,
        "status": "timeout",
        "error": "G.A.I. did not return a decision before gateway timeout",
    }


def _worker() -> None:
    while True:
        with _command_condition:
            rows = _read_queue()
            item = next((r for r in rows if r.get("status", "queued") == "queued"), None)
            if item is None:
                _command_condition.wait(timeout=0.5)
                continue

            # Only one physical G.A.I. command mailbox exists. Never overwrite
            # a request another producer has not received a decision for.
            if _current_command_pending():
                _command_condition.wait(timeout=0.5)
                continue

            item["status"] = "dispatching"
            item["dispatched_at"] = time.time()
            _write_queue(rows)

        request = {
            "id": item["id"],
            "command": item["command"],
            "requested_at": item["requested_at"],
            "source": "agent_gateway",
            "agent_id": item["agent_id"],
            "session_id": item["session_id"],
            "correlation_id": item["correlation_id"],
            "reason": item.get("reason", ""),
        }
        REQUEST.write_text(json.dumps(request, indent=2), encoding="utf-8")
        _audit("command.dispatched", {
            "id": item["id"],
            "correlation_id": item["correlation_id"],
            "agent_id": item["agent_id"],
            "command": item["command"],
        })

        # UserCommandCell evaluates this request on its normal CNS ticks.
        decision = None
        deadline = time.monotonic() + float(_load_config().get("command_timeout_seconds", 45))
        while time.monotonic() < deadline:
            try:
                if RESULT.exists():
                    candidate = json.loads(RESULT.read_text())
                    if str(candidate.get("id", "")) == item["id"]:
                        decision = candidate
                        break
            except Exception:
                pass
            time.sleep(0.2)

        with _command_condition:
            rows = _read_queue()
            for row in rows:
                if row.get("id") == item["id"]:
                    row["status"] = "completed" if decision is not None else "timeout"
                    row["decision"] = decision
                    row["completed_at"] = time.time()
                    if decision is None:
                        row["error"] = "decision timeout"
                    break
            _write_queue(rows)
            _command_condition.notify_all()

        _audit("command.completed" if decision else "command.timeout", {
            "id": item["id"],
            "correlation_id": item["correlation_id"],
            "agent_id": item["agent_id"],
            "command": item["command"],
            "agreed": decision.get("agreed") if decision else None,
        })


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "GAI-Agent-Gateway/1.0"

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(body, dict):
            raise ValueError("JSON object required")
        return body

    def do_GET(self) -> None:
        if self.path == "/health":
            cfg = _load_config()
            self._json(200, {
                "ok": True,
                "service": "gai-agent-gateway",
                "version": "1.0",
                "v1_authority": "central_cognition",
                "physical_command_mailbox": str(REQUEST),
                "multi_agent": True,
                "bound": f"{cfg.get('bind')}:{cfg.get('port')}",
            })
            return
        if self.path == "/agents":
            agents = _load_config().get("agents", {})
            self._json(200, {
                "agents": {
                    k: {
                        "enabled": bool(v.get("enabled", False)),
                        "can_chat": bool(v.get("can_chat", False)),
                        "can_request_commands": bool(v.get("can_request_commands", False)),
                    }
                    for k, v in agents.items()
                    if isinstance(v, dict)
                }
            })
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            body = self._body()

            if self.path == "/v1/chat":
                agent_id = _safe_id(body.get("agent_id"), "agent_id")
                session_id = _safe_id(body.get("session_id", "default"), "session_id")
                policy = _agent_policy(agent_id)
                if not policy.get("enabled") or not policy.get("can_chat"):
                    raise PermissionError("agent is not permitted to chat")
                message = body.get("message")
                if not isinstance(message, str) or not message.strip():
                    raise ValueError("message required")
                context = body.get("gai_context", {})
                if not isinstance(context, dict):
                    raise ValueError("gai_context must be an object")
                correlation_id = _safe_id(
                    body.get("correlation_id", uuid.uuid4().hex),
                    "correlation_id",
                )
                answer = chat(
                    message,
                    context,
                    history_key=f"{agent_id}:{session_id}",
                )
                _audit("chat.completed", {
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                })
                self._json(200, {
                    "ok": True,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "answer": answer,
                })
                return

            if self.path == "/v1/command":
                agent_id = _safe_id(body.get("agent_id"), "agent_id")
                session_id = _safe_id(body.get("session_id", "default"), "session_id")
                policy = _agent_policy(agent_id)
                if not policy.get("enabled") or not policy.get("can_request_commands"):
                    raise PermissionError("agent is not permitted to request commands")
                command = str(body.get("command", "")).strip().lower()
                if command not in ALLOWED_COMMANDS:
                    raise ValueError(f"command must be one of {sorted(ALLOWED_COMMANDS)}")
                correlation_id = _safe_id(
                    body.get("correlation_id", uuid.uuid4().hex),
                    "correlation_id",
                )
                item = {
                    "id": uuid.uuid4().hex,
                    "status": "queued",
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "command": command,
                    "reason": str(body.get("reason", ""))[:500],
                    "requested_at": time.time(),
                }
                result = _submit_command(item)
                self._json(200, {
                    "ok": result.get("status") == "completed",
                    "status": result.get("status"),
                    "request": result,
                })
                return

            self._json(404, {"error": "not found"})
        except PermissionError as e:
            self._json(403, {"error": str(e)})
        except (ValueError, json.JSONDecodeError) as e:
            self._json(400, {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def log_message(self, *_args: Any) -> None:
        pass


def main() -> None:
    cfg = _load_config()
    if not cfg.get("enabled", True):
        raise SystemExit("G.A.I. agent gateway disabled")

    worker = threading.Thread(target=_worker, name="agent-gateway-worker", daemon=True)
    worker.start()

    address = (str(cfg.get("bind", "127.0.0.1")), int(cfg.get("port", 8766)))
    server = ThreadingHTTPServer(address, GatewayHandler)
    print(f"G.A.I. Agent Gateway listening on http://{address[0]}:{address[1]}")
    server.serve_forever()


if __name__ == "__main__":
    main()
