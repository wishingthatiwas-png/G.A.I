from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from .cell import Cell
from .nervous import Event

ROOT = Path("/mnt/gai")
CONFIG = ROOT / "config/user_commands.json"
REQUEST = ROOT / "state/user_command.json"
RESULT = ROOT / "state/user_command_result.json"


class UserCommandCell(Cell):
    """Turns human commands into requests that G.A.I. may accept or decline.

    The human never directly commands an organ here. G.A.I. evaluates the
    request against its current internal state first.
    """

    COMMANDS = {"move", "sleep", "wake"}

    def __init__(self, kernel):
        super().__init__(
            "user_commands",
            kernel.nervous,
            version="1.0.0",
            sleep_phases={"awake", "pre_sleep", "dream", "wake"},
            critical=False,
        )
        self.kernel = kernel
        self._last_request_id = None
        self._last_check = 0.0
        self.listen("tick.started", self.receive, self.sleep_phases)
        self.listen("lifecycle.transition", self.receive, self.sleep_phases)

    def _settings(self) -> dict:
        try:
            return json.loads(CONFIG.read_text())
        except Exception:
            return {
                "enabled": ["move", "sleep", "wake"],
                "agreement": {
                    "move_min_energy": 0.15,
                    "move_max_stress": 0.90,
                    "sleep_min_need": 0.20,
                    "sleep_max_energy": 0.92,
                    "wake_max_sleep_need": 0.85,
                },
            }

    def _read_request(self) -> dict | None:
        try:
            request = json.loads(REQUEST.read_text())
        except Exception:
            return None
        if not isinstance(request, dict):
            return None
        request_id = str(request.get("id", ""))
        if not request_id or request_id == self._last_request_id:
            return None
        return request

    def _write_result(self, request: dict, agreed: bool, reason: str, action: str | None = None):
        result = {
            "id": request.get("id"),
            "command": request.get("command"),
            "agreed": bool(agreed),
            "reason": reason,
            "action": action,
            "timestamp": time.time(),
            "phase": self.kernel.lifecycle.state.phase.value,
        }
        RESULT.write_text(json.dumps(result, indent=2))
        return result

    def evaluate(self, command: str) -> tuple[bool, str]:
        s = self._settings().get("agreement", {})
        command = command.lower()
        phase = self.kernel.lifecycle.state.phase.value
        energy = float(getattr(self.kernel.core_needs, "energy", self.kernel.state.energy))
        stress = float(getattr(self.kernel.state, "stress", 0.0))
        sleep_need = float(getattr(self.kernel.lifecycle.state, "sleep_need", 0.0))
        fatigue = float(getattr(self.kernel.state, "fatigue", 0.0))

        if command == "move":
            if phase != "awake":
                return False, f"I am {phase}; movement is not available."
            if energy < float(s.get("move_min_energy", 0.15)):
                return False, f"My energy is too low ({energy:.2f})."
            if stress > float(s.get("move_max_stress", 0.90)):
                return False, f"My stress is too high ({stress:.2f})."
            return True, f"I agree to move; energy={energy:.2f}, stress={stress:.2f}."

        if command == "sleep":
            if phase != "awake":
                return False, f"I am already {phase}."
            minimum_need = float(s.get("sleep_min_need", 0.20))
            max_energy = float(s.get("sleep_max_energy", 0.92))
            if sleep_need < minimum_need and energy > max_energy and fatigue < 0.80:
                return False, (
                    f"I do not currently need sleep; sleep_need={sleep_need:.2f}, "
                    f"energy={energy:.2f}, fatigue={fatigue:.2f}."
                )
            return True, (
                f"I agree to sleep; sleep_need={sleep_need:.2f}, "
                f"fatigue={fatigue:.2f}."
            )

        if command == "wake":
            if phase == "awake":
                return False, "I am already awake."
            maximum_need = float(s.get("wake_max_sleep_need", 0.85))
            if sleep_need > maximum_need:
                return False, f"I still need sleep; sleep_need={sleep_need:.2f}."
            return True, f"I agree to wake; sleep_need={sleep_need:.2f}."

        return False, "Unknown command."

    def receive(self, event: Event):
        request = self._read_request()
        if not request:
            return
        self._last_request_id = str(request.get("id"))
        command = str(request.get("command", "")).strip().lower()
        settings = self._settings()
        enabled = set(settings.get("enabled", []))

        if command not in self.COMMANDS or command not in enabled:
            result = self._write_result(request, False, "Command is not enabled.")
            self.heartbeat(result)
            return

        agreed, reason = self.evaluate(command)
        action = None

        if agreed:
            if command == "move":
                self.kernel.user_action_request = {
                    "command": "move",
                    "reason": reason,
                    "request_id": request.get("id"),
                }
                action = "move"
                self.kernel.emit(
                    "user.command.accepted",
                    {"command": command, "reason": reason, "request_id": request.get("id")},
                    priority="control",
                    provenance="user_command",
                )
            elif command in {"sleep", "wake"}:
                self.kernel.user_lifecycle_request = {
                    "command": command,
                    "reason": reason,
                    "request_id": request.get("id"),
                }
                action = command
                self.kernel.emit(
                    "user.command.accepted",
                    {"command": command, "reason": reason, "request_id": request.get("id")},
                    priority="control",
                    provenance="user_command",
                )
        else:
            self.kernel.emit(
                "user.command.declined",
                {"command": command, "reason": reason, "request_id": request.get("id")},
                priority="normal",
                provenance="user_command",
            )

        result = self._write_result(request, agreed, reason, action)
        self.heartbeat(result)
