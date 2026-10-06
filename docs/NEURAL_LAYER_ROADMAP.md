# G.A.I. Neural Layer Roadmap

Status: Phase 1 implemented
Date: 2026-10-06

## Purpose

The neural layer is not intended to replace Central Consciousness or the current V1 loop.

It is a plastic substrate underneath future cognition.

The stable loop remains:

    sensation -> salience/attention -> internal state -> competing actions -> action -> consequence -> reward -> memory

The neural layer learns the relationships that emerge inside that loop.

## Phase 1 — Sparse adaptive routing [IMPLEMENTED]

Current unit:

    attended stimulus -> action

Each route contains a bounded adaptive weight, visits, reward history, prediction error, and recency.

Learning uses actual consequences rather than thought frequency.

Awake plasticity is conservative. Pre-sleep and dream plasticity are deliberately larger.

Dream replay consumes recent experience traces and updates routing without requiring a direct CC instruction such as rewire.

Maintenance prunes weak routes and keeps the substrate bounded.

## Phase 2 — Elastic connections [NEXT]

Introduce a distinction between stable routes, temporary routes, and dormant routes.

A novel or strongly rewarding experience may create a temporary pathway.

Repeated useful experiences can promote that pathway toward stability.

Unused pathways should decay toward dormancy rather than disappearing immediately.

This gives G.A.I. a form of forgetting without a hard delete event.

Resource rule: do not allow unbounded route growth. Structural capacity must remain coupled to available energy, memory, and storage pressure.

## Phase 3 — Sleep-dependent plasticity

Sleep becomes the main structural adaptation window.

Proposed sequence:

    pre_sleep -> protect/compact -> dream replay -> route mutation -> pruning -> consolidation -> wake

During pre-sleep, reduce noisy weak plastic changes and prepare recent experience for replay.

During dream, plasticity can expand significantly.

During wake, structural edits should be rare and small.

Waking experience gathers evidence while sleep reorganises the substrate.

## Phase 4 — Dream integration

Dream replay should stop being only associative-memory replay.

It should become a controlled simulation space for replaying recent experiences, replaying high prediction-error events, testing alternative action relationships, combining old and new associations, selectively strengthening successful routes, and weakening repeatedly unsuccessful strategies.

Dreams must remain bounded. No dream process should have unrestricted authority over external hardware or desktop tools.

## Phase 5 — Autonomous maintenance

Maintenance routines should not be scheduled by Central Consciousness as explicit tasks.

They should emerge from lifecycle state and accumulated system pressures.

Candidate maintenance pressures:
- route saturation
- memory pressure
- prediction-error backlog
- repeated failed strategies
- inactive pathways
- storage pressure
- energy availability

CC observes the consequences; it does not have to micromanage maintenance.

## Phase 6 — Experience-shaped neural topology

Once Phase 2–5 are stable, allow topology itself to become adaptive.

Possible changes:
- add a sparse route
- remove a weak route
- split a broad route into context-specific routes
- merge routes that repeatedly converge on the same outcome
- temporarily open cross-modal links when audiovisual synchrony is high

Topology changes must be sparse and measurable.

No opaque large model should be introduced merely to make the system appear more intelligent.

## Phase 7 — Cross-modal neural fabric

Extend routes beyond single-modality labels.

Examples:

    vision:motion + audio:transient -> orient
    vision:social-pattern + internal:social-need -> approach
    audio:novel + boredom:high -> explore

The shared salience field remains upstream.

The neural fabric learns which combinations historically produce useful outcomes.

## Phase 8 — Sleep elasticity

Elasticity becomes a first-class property.

High-load or novel periods may create more temporary structure.

Calm or repetitive periods may allow aggressive consolidation and pruning.

Sleep depth can modulate plasticity.

The exact relationship should be learned experimentally rather than hard-coded as personality.

## Phase 9 — Validation before expansion

Every neural-layer change requires at least one measurable experiment.

Required measurements:
- route count
- route creation rate
- route pruning rate
- average route lifetime
- reward-weight correlation
- prediction-error reduction
- sensory-to-action latency
- memory/storage cost
- CPU cost
- wake vs dream plasticity

A neural feature should stay only when it produces a measurable improvement in behavioural adaptation or efficiency.

## Architectural boundary

The intended long-term hierarchy is:

    organs
    -> sensory compression
    -> shared attention/salience
    -> internal chemistry/homeostasis
    -> neural fabric
    -> Central Consciousness / action selection
    -> motor/output organs
    -> consequence
    -> memory
    -> sleep/dream maintenance
    -> neural adaptation

The neural fabric is therefore a learned substrate, not a second Central Consciousness.

## Immediate next build

Build Phase 2 first:

**elastic connections with temporary -> dormant -> stable states, bounded by resources and altered primarily during sleep/dream.**

Do not add a large neural network yet.

The objective is to make the existing organism’s learned behaviour structurally plastic before increasing representational complexity.