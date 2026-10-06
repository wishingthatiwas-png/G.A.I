# G.A.I. Simplification Audit — 2026-10-06

## Principle
V1 should behave more like a small animal: sense → salience → need/drive → simple choice → action → consequence. Language is an optional communication layer, not the core of cognition.

## Simplify now

### 1. Language/Cognition
- `cognition/core.py` was building a rich language prompt every V1 tick even though no language model is attached.
- V1 now bypasses that prompt on the normal path and calls the model-free policy directly.
- Internal V1 thoughts are now minimal action labels: `rest`, `notice`, `move`, `touch`, `call`, `wait`.
- A language model remains an optional experiment rather than a requirement for the organism.

### 2. Legacy LocalAgent
- `core/agent.py` contained a second autonomous cognition loop, old model/task planning and a second audio-input ownership path.
- V1 now permanently disables the legacy autonomous cognition loop.
- LocalAgent no longer starts a second audio capture path; sensory audio remains owned by the sensory layer.
- Keep the compatibility/socket surface temporarily, but do not let it become a second controller.

## Simplify next (not yet refactored)

### 3. Motivation
`core/motivation.py` currently combines instincts, chemistry, emotions and motivation arbitration. V1 should make needs/drives the control variables; chemistry and emotion should primarily describe internal state/phenotype. Reduce the number of places that can influence action choice.

### 4. Motor/Action Centre
`core/motor_center.py` currently handles movement, focus, habitat interaction, GUI output, creative artifacts and vocalization. Keep one validated motor boundary, but split organ adapters internally so the centre is a router/executor rather than a large collection of behaviours.

### 5. Neural Fabric
The sparse attention/action learner is useful for V1. Population/compute-fabric behaviour should remain subordinate until route usefulness is demonstrated; do not add more neural machinery just because it is available.

### 6. Memory
Memory is comparatively compact. Keep the three-tier direction, but do not add more retrieval machinery until episode formation and continuity are working.

## Explicitly avoid
- Human-style chain-of-thought as an organism mechanism.
- Multiple autonomous decision loops.
- Separate sensor ownership for the same physical device.
- Large language prompts on every low-level cycle.
- Emotion/chemistry modules becoming hidden controllers.
- Complex planning before the simple closed loop is reliable.

## V1 target
**See/hear → notice → want/need → choose one small action → act → feel consequence → learn.**

Speech should sit beside movement as an output behaviour, not above the nervous system as the thing that decides what the organism does.
