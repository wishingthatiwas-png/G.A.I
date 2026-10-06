#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/mnt/gai"
AGENT="$ROOT/agent"
PYTHON="$ROOT/venvs/gai/bin/python"
ACTIVE="$ROOT/state/gai_active.json"
LOCK="$ROOT/state/kernel.lock"
LOG="$ROOT/logs/launcher.log"
KERNEL_PID=""
BUBBLE_PID=""

mkdir -p "$ROOT/state" "$ROOT/logs"
exec >>"$LOG" 2>&1

echo "[$(date -Is)] G.A.I. launcher: preflight"
cd "$AGENT"

[[ -x "$PYTHON" ]] || { echo "G.A.I. launcher: Python environment missing: $PYTHON"; exit 1; }
[[ -f "$AGENT/main.py" ]] || { echo "G.A.I. launcher: main.py missing"; exit 1; }
[[ -f "$AGENT/core/kernel.py" ]] || { echo "G.A.I. launcher: kernel missing"; exit 1; }

kernel_lock_held() {
  "$PYTHON" - <<'PY'
import fcntl
from pathlib import Path
p=Path('/mnt/gai/state/kernel.lock')
f=p.open('a+')
try:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print('1')
else:
    print('0')
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
finally:
    f.close()
PY
}

if [[ -f "$ACTIVE" ]]; then
  active="$("$PYTHON" - <<'PY'
import json
from pathlib import Path
p=Path('/mnt/gai/state/gai_active.json')
try: data=json.loads(p.read_text())
except Exception: data={}
print('1' if data.get('active') else '0')
PY
)"
  if [[ "$active" == "1" ]]; then
    if [[ "$(kernel_lock_held)" == "1" ]]; then
      echo "G.A.I. appears active already; refusing second launch"
      exit 1
    fi
    echo "[$(date -Is)] G.A.I. launcher: clearing stale active marker"
    "$PYTHON" - <<'PY'
import json, time
from pathlib import Path
Path('/mnt/gai/state/gai_active.json').write_text(json.dumps({
    'active': False,
    'stopped_by': 'stale_marker_recovery',
    'stopped': time.time(),
}))
PY
  fi
fi

if [[ "$(kernel_lock_held)" == "1" ]]; then
  echo "G.A.I. kernel lock is held by another process"
  exit 1
fi

echo "[$(date -Is)] G.A.I. launcher: starting organism"
export PYTHONPATH="$AGENT${PYTHONPATH:+:$PYTHONPATH}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/null/.Xauthority}"
# CUDA neural backend: G's GTX 950M uses the CUDA 12 NVRTC runtime shipped in the G.A.I. venv.
CUDA_NVRTC="$ROOT/venvs/gai/lib/python3.12/site-packages/nvidia/cuda_nvrtc"
if [[ -d "$CUDA_NVRTC" ]]; then
  export CUDA_PATH="$CUDA_NVRTC"
  export LD_LIBRARY_PATH="$CUDA_NVRTC/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

start_bubble() {
  local existing=""
  existing=$(pgrep -f "$AGENT/gui/monitor.py" | head -1 || true)
  if [[ "$existing" =~ ^[0-9]+$ ]] && kill -0 "$existing" 2>/dev/null; then
    BUBBLE_PID="$existing"
  else
    "$PYTHON" "$AGENT/gui/monitor.py" >>"$ROOT/logs/bubble.log" 2>&1 &
    BUBBLE_PID=$!
  fi
  echo "$BUBBLE_PID" > "$ROOT/state/bubble.pid"
}

shutdown() {
  local code=$?
  echo "[$(date -Is)] G.A.I. launcher: shutdown (code=$code)"
  if [[ -n "$KERNEL_PID" ]] && kill -0 "$KERNEL_PID" 2>/dev/null; then
    kill -TERM "$KERNEL_PID" 2>/dev/null || true
    for _ in {1..20}; do
      kill -0 "$KERNEL_PID" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$KERNEL_PID" 2>/dev/null || true
  fi
  # The kernel's intentional metabolic worker inherits the kernel lock; reap it too.
  pkill -TERM -f '/mnt/gai/agent/main.py' 2>/dev/null || true
  sleep 0.2
  pkill -KILL -f '/mnt/gai/agent/main.py' 2>/dev/null || true
  if [[ -n "$BUBBLE_PID" ]] && kill -0 "$BUBBLE_PID" 2>/dev/null; then
    kill -TERM "$BUBBLE_PID" 2>/dev/null || true
    for _ in {1..20}; do
      kill -0 "$BUBBLE_PID" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$BUBBLE_PID" 2>/dev/null || true
  fi
  rm -f "$ROOT/state/bubble.pid" "$ROOT/state/kernel.pid"
  # Physical/output organs are children of the organism but may outlive it if
  # the launcher receives an external termination signal.
  if [[ -f "$ROOT/state/output_windows.pid" ]]; then
    opid=$(cat "$ROOT/state/output_windows.pid" 2>/dev/null || true)
    [[ "$opid" =~ ^[0-9]+$ ]] && kill -TERM "$opid" 2>/dev/null || true
    rm -f "$ROOT/state/output_windows.pid"
  fi
  pkill -TERM -f '/mnt/gai/agent/gui/toy_app.py' 2>/dev/null || true
  pkill -TERM -f '/mnt/gai/agent/gui/output_windows.py' 2>/dev/null || true
  pkill -TERM -f '/mnt/gai/agent/gui/focus_bubble.py' 2>/dev/null || true
  pkill -TERM -f '/mnt/gai/agent/perception/screen_stream.py' 2>/dev/null || true
  pkill -TERM -f '/mnt/gai/agent/gui/display_guard.py' 2>/dev/null || true
  pkill -TERM -f '/mnt/gai/agent/gui/speaker_organ.py' 2>/dev/null || true
  pkill -TERM -f 'pw-record --rate 48000 --channels 2' 2>/dev/null || true
  "$PYTHON" - <<'PY' || true
import json, time
from pathlib import Path
Path('/mnt/gai/state/gai_active.json').write_text(json.dumps({'active': False, 'stopped_by': 'launcher', 'stopped': time.time()}))
PY
  exit "$code"
}

trap 'exit 143' TERM INT
trap shutdown EXIT

"$PYTHON" "$AGENT/main.py" &
KERNEL_PID=$!
echo "$KERNEL_PID" > "$ROOT/state/kernel.pid"
start_bubble
wait "$KERNEL_PID"
code=$?
KERNEL_PID=""
exit "$code"
