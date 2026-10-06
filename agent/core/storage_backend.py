"""Pluggable long-term storage backends for G.A.I.

V1 deliberately uses only a local SSD-backed backend.  The interface is kept
small so a future HDD or cloud backend can be added without changing memory
semantics or cognition.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class StorageBackend:
    """Interface for durable memory-bank storage."""

    name = "abstract"

    def write(self, memory_id: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError

    def read(self, memory_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def exists(self, memory_id: str) -> bool:
        raise NotImplementedError

    def manifest(self) -> dict[str, Any]:
        return {"backend": self.name}


class LocalSSDBackend(StorageBackend):
    """Current V1 memory organ: a bounded, inspectable SSD directory."""

    name = "ssd"

    def __init__(self, root: str | Path = "/mnt/gai/memory"):
        self.root = Path(root)
        self.bank_root = self.root / "banks"
        self.memory_root = self.bank_root / "long_term"
        self.manifest_path = self.bank_root / "manifest.json"
        self.memory_root.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self._write_manifest()

    def _write_manifest(self):
        payload = {
            "schema": 1,
            "backend": self.name,
            "root": str(self.root),
            "created_at": time.time(),
            "expansion": ["hdd", "cloud"],
        }
        tmp = self.manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        tmp.replace(self.manifest_path)

    def write(self, memory_id: str, payload: dict[str, Any]) -> str:
        target = self.memory_root / f"{memory_id}.json"
        envelope = {
            "schema": 1,
            "memory_id": memory_id,
            "storage": self.name,
            "committed_at": time.time(),
            "sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest(),
            "payload": payload,
        }
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(envelope, sort_keys=True, indent=2))
        tmp.replace(target)
        return str(target)

    def read(self, memory_id: str) -> dict[str, Any] | None:
        target = self.memory_root / f"{memory_id}.json"
        if not target.exists():
            return None
        try:
            envelope = json.loads(target.read_text())
            payload = envelope.get("payload", envelope)
            expected = envelope.get("sha256")
            if expected:
                actual = hashlib.sha256(
                    json.dumps(payload, sort_keys=True).encode()
                ).hexdigest()
                if actual != expected:
                    return None
            return payload
        except (OSError, ValueError, TypeError):
            return None

    def exists(self, memory_id: str) -> bool:
        return (self.memory_root / f"{memory_id}.json").exists()

    def manifest(self) -> dict[str, Any]:
        try:
            return json.loads(self.manifest_path.read_text())
        except Exception:
            return {"schema": 1, "backend": self.name, "root": str(self.root)}


class HddBackend(StorageBackend):
    """Future detachable HDD backend placeholder; intentionally inactive in V1."""

    name = "hdd"

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def write(self, memory_id, payload):
        raise RuntimeError("HDD backend is not enabled in V1")

    def read(self, memory_id):
        raise RuntimeError("HDD backend is not enabled in V1")

    def exists(self, memory_id):
        return False


class CloudBackend(StorageBackend):
    """Future remote/cloud backend placeholder; intentionally inactive in V1."""

    name = "cloud"

    def write(self, memory_id, payload):
        raise RuntimeError("Cloud backend is not enabled in V1")

    def read(self, memory_id):
        raise RuntimeError("Cloud backend is not enabled in V1")

    def exists(self, memory_id):
        return False
