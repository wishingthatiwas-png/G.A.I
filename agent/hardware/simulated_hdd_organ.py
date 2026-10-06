"""SSD-backed simulation of G.A.I.'s detachable HDD organ.

The organism still treats this as an organ with an attach/verify/detach boundary.
For the laptop experiment the physical medium is replaced by a directory on the
SSD. No real block device operations are performed.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path("/mnt/gai")


@dataclass
class SimulatedHDDState:
    present: bool = True
    verified: bool = False
    attached: bool = False
    mounted: bool = False
    writable: bool = False
    status: str = "absent"
    organ_id: str = "simulated-hdd-ssd-v1"
    backing_path: str = str(ROOT / "storage" / "simulated_hdd")
    last_change: float = 0.0
    error: str | None = None


class SimulatedHDDOrgan:
    """A removable-HDD-like organ backed by an ordinary SSD directory."""

    FORMAT = "gai-simulated-hdd-organ"

    def __init__(self, backing_path: str | Path = ROOT / "storage" / "simulated_hdd",
                 state_path: str | Path = ROOT / "state" / "simulated_hdd_organ.json"):
        self.backing = Path(backing_path)
        self.state_path = Path(state_path)
        self.state = SimulatedHDDState(backing_path=str(self.backing), last_change=time.time())
        self._load()
        self.provision()

    def _load(self):
        try:
            if self.state_path.exists():
                self.state = SimulatedHDDState(**json.loads(self.state_path.read_text()))
        except (OSError, ValueError, TypeError):
            pass

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self.state), indent=2) + "\n")
        tmp.replace(self.state_path)

    def provision(self):
        self.backing.mkdir(parents=True, exist_ok=True)
        manifest = self.backing / "ORGAN.json"
        if not manifest.exists():
            payload = {
                "format": self.FORMAT,
                "organ_id": self.state.organ_id,
                "created": time.time(),
                "medium": "ssd-simulation",
                "purpose": "replace detachable HDD while developing the organism",
            }
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            payload["sha256"] = hashlib.sha256(raw).hexdigest()
            manifest.write_text(json.dumps(payload, indent=2) + "\n")
        self.state.present = True
        self.state.last_change = time.time()
        self._save()

    def attach(self) -> dict:
        if not self.backing.exists():
            self.provision()
        self.state.attached = True
        self.state.mounted = True
        self.state.writable = False
        self.state.status = "attached"
        self.state.last_change = time.time()
        self._save()
        return self.snapshot()

    def verify(self) -> bool:
        try:
            data = json.loads((self.backing / "ORGAN.json").read_text())
            ok = data.get("format") == self.FORMAT and data.get("organ_id") == self.state.organ_id
            self.state.verified = bool(ok)
            self.state.status = "verified" if ok else "invalid"
            self.state.error = None if ok else "invalid simulated HDD manifest"
        except (OSError, ValueError, TypeError) as exc:
            self.state.verified = False
            self.state.status = "error"
            self.state.error = str(exc)
        self.state.last_change = time.time()
        self._save()
        return self.state.verified

    def begin_write(self):
        if not (self.state.present and self.state.attached and self.state.mounted and self.state.verified):
            raise RuntimeError("simulated HDD organ is not attached and verified")
        self.state.writable = True
        self.state.status = "writable"
        self.state.last_change = time.time()
        self._save()

    def end_write(self):
        self.state.writable = False
        if self.state.attached:
            self.state.status = "attached"
        self.state.last_change = time.time()
        self._save()

    def detach(self):
        self.state.attached = False
        self.state.mounted = False
        self.state.verified = False
        self.state.writable = False
        self.state.status = "detached"
        self.state.last_change = time.time()
        self._save()

    def simulate_failure(self):
        """Simulate an absent organ without deleting the backing data."""
        self.state.present = False
        self.state.attached = False
        self.state.mounted = False
        self.state.verified = False
        self.state.writable = False
        self.state.status = "absent"
        self.state.last_change = time.time()
        self._save()

    def restore(self):
        self.state.present = True
        self.state.status = "restored"
        self.state.last_change = time.time()
        self._save()
        self.provision()

    def clear_simulation(self):
        """Test helper: erase only the simulated organ directory."""
        if self.backing.exists():
            shutil.rmtree(self.backing)
        self.state = SimulatedHDDState(backing_path=str(self.backing), last_change=time.time())
        self._save()

    def snapshot(self) -> dict:
        return asdict(self.state)
