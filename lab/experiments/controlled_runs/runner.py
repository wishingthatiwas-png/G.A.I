#!/usr/bin/env python3
"""G.A.I. controlled experiment runner.

Design:
  X = one controlled variable
  Y = measured response metrics
  Z = elapsed time/checkpoint

Each run gets a fresh run directory and immutable baseline metadata. The runner
does not modify G.A.I.'s cognitive code; it only records state and host telemetry.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/mnt/gai")
STATE = ROOT / "state/runtime.json"
RUNS = ROOT / "lab/experiments/controlled_runs"

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def host_metrics():
    cmds = {
        "load": "cat /proc/loadavg",
        "memory": "free -b",
        "uptime": "uptime -s",
        "power_profile": "powerprofilesctl get",
        "temperature": "sensors -j 2>/dev/null || true",
    }
    out = {}
    for k, cmd in cmds.items():
        try:
            out[k] = subprocess.run(["bash","-lc",cmd], capture_output=True, text=True, timeout=3).stdout
        except Exception as e:
            out[k] = f"ERROR: {e}"
    return out

def snapshot(run_dir, label, started):
    state = read_json(STATE)
    record = {
        "timestamp": now(),
        "label": label,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "gai_state": state,
        "host": host_metrics(),
    }
    path = run_dir / f"{label}.json"
    path.write_text(json.dumps(record, indent=2))
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--variable", default="baseline")
    ap.add_argument("--value", default="control")
    ap.add_argument("--duration", type=int, default=300)
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    run_dir = RUNS / args.run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()

    meta = {
        "run_id": args.run_id,
        "started": now(),
        "variable_changed": args.variable,
        "value": args.value,
        "duration_seconds": args.duration,
        "checkpoint_interval_seconds": args.interval,
        "notes": args.notes,
        "design": {"x": "controlled variable", "y": "measured response", "z": "elapsed time"},
        "baseline_rule": "restart from the same baseline; change exactly one variable",
    }
    (run_dir / "manifest.json").write_text(json.dumps(meta, indent=2))
    snapshot(run_dir, "t0", started)

    deadline = time.monotonic() + args.duration
    i = 1
    while time.monotonic() < deadline:
        time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
        snapshot(run_dir, f"t{i:03d}", started)
        i += 1

    snapshot(run_dir, "final", started)
    meta["finished"] = now()
    meta["checkpoints"] = i
    (run_dir / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(f"Completed {args.run_id}: {run_dir}")

if __name__ == "__main__":
    main()
