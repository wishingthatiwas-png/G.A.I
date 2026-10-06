"""Compressed SSD deep-storage memory banks.

Storage capacity is governed by the filesystem, not metabolic worker count.
Workers affect processing/recall bandwidth elsewhere in the organism.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
from pathlib import Path


class DeepStorageError(RuntimeError):
    pass


class MemoryBank:
    FORMAT = "gai-memory-bank-v1"

    def __init__(self, root: str | Path = "/mnt/gai/storage/simulated_hdd/deep_storage"):
        self.root = Path(root)

    def create(self, bank_id: str, purpose: str = "deep-memory") -> Path:
        if not bank_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in bank_id):
            raise DeepStorageError("invalid bank id")
        bank = self.root / bank_id
        bank.mkdir(parents=True, exist_ok=True)
        manifest = bank / "manifest.json"
        if not manifest.exists():
            manifest.write_text(json.dumps({
                "format": self.FORMAT,
                "bank_id": bank_id,
                "purpose": purpose,
                "created": time.time(),
                "compression": "gzip",
                "record_encoding": "jsonl",
                "records": 0,
                "bytes_raw": 0,
                "bytes_compressed": 0,
            }, indent=2) + "\n")
        return bank

    def append(self, bank_id: str, records: list[dict]) -> dict:
        bank = self.create(bank_id)
        if not records:
            return self.stats(bank_id)
        path = bank / "records.jsonl.gz"
        raw_lines = b"".join((json.dumps(r, sort_keys=True, separators=(",", ":")).encode() + b"\n") for r in records)
        with gzip.open(path, "ab", compresslevel=9) as f:
            f.write(raw_lines)
        manifest_path = bank / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["records"] += len(records)
        manifest["bytes_raw"] += len(raw_lines)
        manifest["bytes_compressed"] = path.stat().st_size
        manifest["updated"] = time.time()
        manifest["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        tmp = manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, indent=2) + "\n")
        tmp.replace(manifest_path)
        return manifest

    def read(self, bank_id: str) -> list[dict]:
        path = self.root / bank_id / "records.jsonl.gz"
        if not path.exists():
            return []
        with gzip.open(path, "rb") as f:
            data = f.read().decode()
        return [json.loads(line) for line in data.splitlines() if line.strip()]

    def validate(self, bank_id: str) -> dict:
        bank = self.root / bank_id
        manifest = json.loads((bank / "manifest.json").read_text())
        records = self.read(bank_id)
        path = bank / "records.jsonl.gz"
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        return {
            "ok": manifest.get("format") == self.FORMAT
                   and manifest.get("records") == len(records)
                   and manifest.get("sha256") == digest,
            "bank_id": bank_id,
            "manifest_records": manifest.get("records"),
            "decoded_records": len(records),
            "raw_bytes": manifest.get("bytes_raw", 0),
            "compressed_bytes": manifest.get("bytes_compressed", 0),
            "compression_ratio": (
                manifest.get("bytes_raw", 0) / max(1, manifest.get("bytes_compressed", 0))
            ),
        }

    def stats(self, bank_id: str) -> dict:
        bank = self.root / bank_id
        manifest = json.loads((bank / "manifest.json").read_text())
        return manifest
