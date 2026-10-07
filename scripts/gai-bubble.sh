#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/mnt/gai
PYTHON="$ROOT/venvs/gai/bin/python"
LOG="$ROOT/logs/bubble-supervisor.log"
PID="$ROOT/state/gai_supervisor.pid"
mkdir -p "$ROOT/state" "$ROOT/logs"
exec >>"$LOG" 2>&1

echo "[$(date -Is)] G.A.I. bubble supervisor: $*"
case "${1:-start}" in
  start)
    if [[ -f "$PID" ]] && kill -0 "$(cat "$PID" 2>/dev/null || echo 0)" 2>/dev/null; then
      echo "G.A.I. bubble already running"; exit 0
    fi
    nohup "$ROOT/scripts/run-gai.sh" start >/dev/null 2>&1 &
    echo $! > "$PID"
    echo "G.A.I. bubble started"
    ;;
  stop)
    "$ROOT/scripts/run-gai.sh" stop || true
    rm -f "$PID"
    echo "G.A.I. bubble stopped"
    ;;
  restart)
    "$0" stop || true
    sleep 1
    exec "$0" start
    ;;
  status)
    "$ROOT/scripts/run-gai.sh" status || true
    ;;
  *) echo "Usage: $0 {start|stop|restart|status}"; exit 2;;
esac
