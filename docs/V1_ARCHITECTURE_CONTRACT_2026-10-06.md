# G.A.I. V1 Architecture Contract

Date: 2026-10-06
Status: FROZEN FOR V1 ACCEPTANCE

## 1. Canonical organism path

Senses → Nervous System → Neural Workspace / Attention → CC-V1 → Action / Motor → Organs → World / Consequence → Reward → Memory.

No alternate autonomous cognition loop may become authoritative during V1.

## 2. Ownership

### Senses
Reports bounded observations from vision, hearing, body and environment. Senses do not choose actions.

### Nervous System
Routes, gates, prioritises, queues and traces events. It does not decide goals.

### Neural Workspace / Attention
Compresses sensory information, selects what matters and exposes the selected workspace to CC. Neural Fabric is the V1 attention authority.

### CC-V1
Chooses an intention from the current workspace, needs, wants, motivation, state and learned context. CC does not directly control hardware.

### Action / Motor
Validates and executes structured intentions through bounded motor/output primitives. It returns execution results and proprioceptive/consequence events.

### Organs
Perform physical/digital I/O. They report health and outcomes through the nervous system.

### Memory
Stores meaningful episodes, learned preferences and persistent identity/context. Memory does not directly execute actions.

## 3. Core contracts

### Sensory event
Required: source, modality, timestamp, bounded payload, salience/novelty when applicable, correlation_id.

### Neural workspace
Required: selected attention, candidates when available, authority, salience/learned weighting, correlation_id inherited from the active cycle.

### CC intention
Required: type, target, reason, confidence/prediction where available, cycle/correlation identifier. An intention is never a raw hardware command.

### Motor command
Required: validated primitive, bounded target/parameters, reason, correlation/cycle identifier, execution status.

### Outcome / consequence
Required: action reference, success/failure, observed result, timestamp and correlation identifier when available.

### Reward / learning event
Required: action/outcome reference, reward value, prediction error when available, context and correlation identifier.

### Memory event
Required: meaningful experience payload, action/outcome context, salience/reward metadata and persistence tier.

## 4. V1 authority rules

1. One production kernel owns the organism lifecycle.
2. Neural Fabric owns V1 attention selection.
3. CC owns high-level intention selection.
4. Motor Action Centre owns execution.
5. Organs never bypass the Action/Motor boundary for autonomous behaviour.
6. Model services, when enabled, are subordinate cognition providers; CC validates their output.
7. Diagnostics remain external observers.
8. Capability/toy applications remain external environment/tools, not organism control systems.
9. Legacy controllers may remain in source history but cannot be authoritative in V1.
10. Every meaningful closed-loop cycle should remain traceable by correlation ID.

## 5. Verified Gate 0 evidence

- Kernel has an exclusive `state/kernel.lock`.
- V1 tick performs one neural attention selection followed by one `CognitiveCore.think()` decision opportunity.
- Motor Action Centre receives structured intentions and owns execution.
- V1 motor background exploration loop is disabled by the V1 mode guard; autonomous movement is therefore not a second CC loop.
- Diagnostic is external to the organism.
- Agent tree compile check passed.
- Existing V1 attention authority and correlated trace are already live.

## 6. Freeze boundary

Phase 7 changes should improve reliability, testing, recovery, observability or release documentation. Do not introduce new major organs, alternate cognition paths, large neural expansion, metacognition or evolutionary systems during V1 acceptance.

## Gate 0 result

ARCHITECTURE FROZEN. Proceed to Gate 1: prove the input organs end-to-end.
