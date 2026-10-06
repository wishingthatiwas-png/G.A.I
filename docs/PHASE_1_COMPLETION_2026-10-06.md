# G.A.I. Phase 1 — V1 Shape Lock

Date: 2026-10-06
Snapshot: `gai-V1-0.75-20261006-224023.tar.gz`

## Status

**COMPLETE**

Phase 1 is the architecture-lock phase from `MASTER_BUILD_PLAN_2026-10-06.md`: stop moving the core pieces around and establish one unambiguous organism path.

## Locked V1 path

`Senses → Nervous System → Neural Workspace/Attention → CC-V1 → Action/Motor → Organs → Consequence → Reward → Memory`

CC remains the decision authority. The neural layer supplies attention/routing and learning signals; it does not become a second controller. Diagnostic tooling remains external.

## Evidence

- Python compilation of the complete agent tree: **PASS**.
- Automated regression suite excluding the known physical-camera pytest limitation: **65 passed, 0 failed**.
- The live kernel already exposes a correlated perception → attention → cognition → motor → outcome → memory trace.
- Neural Fabric is now in the V1 selection path; V1 attention reports `authority=neural_fabric` in live runtime.
- Hardware-normalized clock is locked at the current 2.5 FPS base tick with simulation speed separate from metabolic cadence.
- Lifecycle wake completion now has an explicit recovery/completion boundary.
- Compatibility fallback remains available for isolated CC tests without a Neural Fabric instance.
- Existing historical project files were preserved; no development documents were deleted or replaced.

## Known hardware-test exception

`agent/tests/test_camera.py` cannot open `/dev/video0` from the pytest process on this laptop. The physical camera organ is independently live and captures successfully. This remains a hardware-contract/test-environment issue for the next input-organ gate, not an architecture-lock failure.

## Phase 2 handoff

Do not refactor the locked core shape. Proceed to explicit **Needs**: Energy, Rest, Safety, Stimulation, Social, Interaction, Exploration and Maintenance.
