"""Detachable deep-memory archive interface.

Phase 1 deliberately does not mount arbitrary devices. It provides the safe
archive lifecycle and docking state machine that a future udev/system mount
layer can call. Deep-memory writes are permitted only during DREAM.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


class ArchiveError(RuntimeError):
    pass


@dataclass
class DockState:
    attached: bool = False
    verified: bool = False
    mounted: bool = False
    writable: bool = False
    phase: str = "awake"
    archive_id: str | None = None
    mount_path: str | None = None
    last_error: str | None = None
    last_change: float = 0.0


class DeepArchive:
    """Represents the removable long-term memory organ."""

    def __init__(self, base: str | Path = "/mnt/gai/archive", state_file: str | Path | None = None):
        self.base = Path(base)
        self.state_file = Path(state_file or self.base / "docking" / "state.json")
        self.state = DockState(last_change=time.time())
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                self.state = DockState(**json.loads(self.state_file.read_text()))
            except (OSError, ValueError, TypeError):
                self.state = DockState(last_change=time.time())

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self.state), indent=2) + "\n")
        tmp.replace(self.state_file)

    def set_phase(self, phase: str):
        if phase not in {"awake", "pre_sleep", "dream", "wake"}:
            raise ValueError(f"unknown phase: {phase}")
        self.state.phase = phase
        if phase != "dream":
            self.state.writable = False
        self.state.last_change = time.time()
        self._save_state()

    def attach(self, archive_id: str, mount_path: str):
        """Register an already-mounted, externally verified archive."""
        if not archive_id or not mount_path:
            raise ArchiveError("archive identity and mount path are required")
        self.state.attached = True
        self.state.verified = False
        self.state.mounted = True
        self.state.writable = False
        self.state.archive_id = archive_id
        self.state.mount_path = mount_path
        self.state.last_error = None
        self.state.last_change = time.time()
        self._save_state()

    def verify_manifest(self, manifest_path: str | Path) -> bool:
        p = Path(manifest_path)
        try:
            data = json.loads(p.read_text())
            ok = bool(data.get("archive_id")) and data.get("format") == "gai-deep-memory"
        except (OSError, ValueError, TypeError):
            ok = False
        self.state.verified = ok
        self.state.last_error = None if ok else "invalid deep-memory manifest"
        self.state.last_change = time.time()
        self._save_state()
        return ok

    def begin_dream_write(self):
        if not (self.state.attached and self.state.verified and self.state.mounted):
            raise ArchiveError("deep archive is not attached and verified")
        if self.state.phase != "dream":
            raise ArchiveError("deep-memory writes are only allowed during DREAM")
        self.state.writable = True
        self.state.last_change = time.time()
        self._save_state()

    def end_dream_write(self):
        self.state.writable = False
        self.state.last_change = time.time()
        self._save_state()

    def commit_memory(self, memory_id: str, payload: dict) -> Path:
        if not self.state.writable:
            raise ArchiveError("deep archive is not writable outside DREAM")
        if not memory_id:
            raise ArchiveError("memory_id required")
        target_root = Path(self.state.mount_path) / "memories"
        target_root.mkdir(parents=True, exist_ok=True)
        record = {"memory_id": memory_id, "created": time.time(), "payload": payload}
        raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
        record["sha256"] = hashlib.sha256(raw).hexdigest()
        target = target_root / f"{memory_id}.json"
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, indent=2) + "\n")
        tmp.replace(target)
        return target

    def detach(self):
        """Forget the mounted archive; actual OS unmount is intentionally external."""
        self.state.attached = False
        self.state.verified = False
        self.state.mounted = False
        self.state.writable = False
        self.state.archive_id = None
        self.state.mount_path = None
        self.state.last_change = time.time()
        self._save_state()

    def snapshot(self) -> dict:
        return asdict(self.state)
