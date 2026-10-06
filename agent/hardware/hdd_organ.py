"""Physical detachable HDD organ for G.A.I.

Safe by design: discovers and identifies the dedicated deep-memory disk but
never formats, partitions, mounts, executes, or writes to an attached device.
OS mount/detach remains an explicit external operation.
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path("/mnt/gai")


@dataclass
class HDDState:
    present: bool = False
    verified: bool = False
    device: str | None = None
    model: str | None = None
    serial: str | None = None
    filesystem: str | None = None
    label: str | None = None
    uuid: str | None = None
    mountpoint: str | None = None
    writable: bool = False
    status: str = "absent"
    last_scan: float = 0.0
    error: str | None = None


class HDDOrgan:
    """Detachable deep-memory organ; identification only until explicitly mounted."""

    def __init__(self, config_path: str | Path = ROOT / "config/agent.json",
                 state_path: str | Path = ROOT / "state/hdd_organ.json"):
        self.config_path = Path(config_path)
        self.state_path = Path(state_path)
        self.state = HDDState()
        self.scan()

    def _config(self) -> dict:
        try:
            return json.loads(self.config_path.read_text())
        except (OSError, ValueError, TypeError):
            return {}

    def _expected(self) -> dict:
        return self._config().get("hdd_organ", {})

    def scan(self) -> dict:
        self.state.last_scan = time.time()
        try:
            raw = subprocess.check_output(
                ["lsblk", "-J", "-o",
                 "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL,SERIAL"],
                text=True, timeout=3,
            )
            data = json.loads(raw)
            expected = self._expected()
            expected_serial = expected.get("serial")
            expected_model = expected.get("model")

            candidates = []
            def walk(nodes):
                for n in nodes:
                    if n.get("type") == "disk":
                        candidates.append(n)
                    walk(n.get("children", []))
            walk(data.get("blockdevices", []))

            match = next(
                (n for n in candidates
                 if expected_serial and n.get("serial") == expected_serial),
                None,
            )
            if match is None and expected_model:
                model_matches = [n for n in candidates if n.get("model") == expected_model]
                if len(model_matches) == 1:
                    match = model_matches[0]

            if match is None:
                self.state = HDDState(
                    present=False, status="absent",
                    last_scan=self.state.last_scan,
                )
            else:
                verified = bool(expected_serial and match.get("serial") == expected_serial)
                mountpoints = match.get("mountpoints") or []
                mountpoint = next((m for m in mountpoints if m), None)
                self.state = HDDState(
                    present=True,
                    verified=verified,
                    device=match.get("path"),
                    model=match.get("model"),
                    serial=match.get("serial"),
                    filesystem=match.get("fstype"),
                    label=match.get("label"),
                    uuid=match.get("uuid"),
                    mountpoint=mountpoint,
                    writable=False,
                    status=("mounted" if mountpoint else
                            "verified" if verified else "unverified"),
                    last_scan=self.state.last_scan,
                )
        except Exception as exc:
            self.state.present = False
            self.state.status = "error"
            self.state.error = str(exc)
        self._save()
        return asdict(self.state)

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self.state), indent=2) + "\n")
        tmp.replace(self.state_path)

    def snapshot(self) -> dict:
        return asdict(self.state)
