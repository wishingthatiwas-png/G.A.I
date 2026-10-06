# Controlled 3D Experiment Matrix

Every run is independent. Restart G.A.I. from the same baseline between runs.

## Axes

- **X — variable:** exactly one manipulated variable per run.
- **Y — response:** runtime state, prediction count, observations, reward, nervous-system errors/drops, host load, memory use, temperature and power profile.
- **Z — time:** fixed checkpoints from T0 onward.

## Initial run set

| Run | X variable | Level | Purpose |
|---|---|---:|---|
| B0 | none | control | baseline |
| M1 | memory/energy | low | lower retained-state condition |
| M2 | memory/energy | high | higher retained-state condition |
| P1 | power/food | low | reduced available power |
| P2 | power/food | high | increased available power |
| W1 | workload | low | light cognitive workload |
| W2 | workload | high | heavy cognitive workload |

Only one X-axis condition changes per run. Duration and checkpoint interval remain fixed unless the protocol explicitly says otherwise.

## Safety rule

Do not intentionally drive the physical machine into thermal, electrical or resource limits. A system crash is an observed outcome, not a target.

## Runner

runner.py records an immutable manifest plus T0, periodic and final snapshots. It does not alter G.A.I.'s cognitive modules.

Suggested first run:

python3 /mnt/gai/lab/experiments/controlled_runs/runner.py --run-id B0 --variable baseline --value control --duration 300 --interval 30
