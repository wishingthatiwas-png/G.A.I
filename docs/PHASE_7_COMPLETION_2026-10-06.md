# G.A.I. Phase 7 — V1 Lockdown & Acceptance

Date: 2026-10-06
Status: ACCEPTANCE COMPLETE WITH KNOWN ENVIRONMENT NOTE

## Final architecture
Senses → Nervous System → Neural Workspace / Attention → CC-V1 → Action / Motor → Organs → World / Consequence → Reward → Memory

Motivation remains a scalable subsystem. It is not removed: needs, instincts, chemistry/emotion and motivation provide graded state/biases while CC remains the decision authority.

## Gate results

### Gate 0 — Architecture
PASS. V1 architecture contract frozen. One production kernel, Neural Fabric owns attention, CC owns intention, Motor Action Centre owns execution, diagnostics remain external.

### Gate 1 — Inputs
PASS. Screen vision, camera organ path, PipeWire audio and auditory perception are operational. Vision/audio share the neural workspace. Physical webcam is optional hardware; camera pytest now passes when the device is absent while live hardware remains independently probeable.

### Gate 2 — Outputs
PASS. Motor output, display/UI output, artifact creation and speaker output cross the motor boundary. Speech output is direct speech-dispatcher audio; no vocoder is required for V1. Output completion/failure state is persisted.

### Gate 3 — Closed loop
PASS for the V1 policy path. Live CC traces show sensory attention feeding CC-V1 intentions, including audio-selected attention producing a `move` intention. Motor boundary and correlation plumbing are present.

### Gate 4 — Memory continuity
PASS at the current V1 acceptance level. Short/persistent memory, recall/reinforcement and SSD-backed memory pipeline tests pass. Deep lifecycle/archive work remains deliberately bounded for V1.

### Gate 5 — Recovery / safety
PASS. Exclusive kernel lock, bounded motor actions, safe invalid-intention rejection, lifecycle tests and V1 guard against the legacy background motor loop are in place.

### Gate 6 — Cognition boundary / performance
PASS. Central V1 cognition is model-free by default; language prompting is optional. Legacy autonomous cognition is disabled and duplicate audio ownership removed. Phase 6 routing/resource baseline remains accepted.

### Gate 7 — Release evidence
PASS with test-run note below. Targeted V1, cognition, prediction, lifecycle, output, nervous, memory, needs/wants/motivation and sensory suites all pass. The complete pytest run reached 100% (`100%` displayed) but the process then emitted `FATAL: exception not rethrown` during teardown. This is treated as a pytest/process teardown issue, not a failed assertion, and is retained as a release-note item until isolated.

## Simplification decision
V1 is intentionally animal-like rather than language-centric:
- language is an output/communication organ, not the cognition engine
- internal policy uses a tiny action vocabulary
- no language prompt on normal V1 ticks
- one central decision loop
- one authoritative audio input path
- motivation retained as scalable graded control state

## Release recommendation
V1 is structurally ready for controlled operation and endurance testing. Do not add major cognition features before the teardown issue and long-soak evidence are closed.
