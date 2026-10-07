# G.A.I. Simple Build Plan — 2026-10-06

This is the current execution plan.

Detailed implementation HOW belongs in the step's working session.
Audit documents record what has already been tested and should be consulted before changing an area.

## Current execution state — 2026-10-07

The plan remains V1-first. The architecture is frozen; the immediate job is **acceptance evidence**, not adding major organs.

### What is now locked
- V1 authority chain: Senses → Nervous System → Neural Workspace/Attention → CC-V1 → Action/Motor → Organs → Consequence → Reward → Memory.
- Bubble is an **output organ**, not the runtime/container.
- V1 visual perception is **inward_virtual**: physical webcam access is disabled and archived; the persistent screen stream is the sole visual input.
- Nervous transport targets 20 Hz; central cognition is bounded to its own cadence so expensive CC work cannot monopolise the nervous clock.
- Multi-agent interaction uses one physical Remote transport plus a loopback Agent Gateway. External agents do not become competing cognition loops.
- Historical/development files are archived rather than deleted.

### Measured state
- Screen-only sensory regression passes.
- Live screen visual frame was fresh (~0.08 s) with mode=in.
- No webcam capture process was running after the inward-vision transition.
- PerceptionCell measured ~38.8 ms/call after the inward-vision change, versus ~77.6 ms/call in the preceding runtime — roughly a 50% reduction.
- Two legacy kernel tests currently fail because they assume cognition completes inside one tick. These are scheduler-contract test failures, not evidence that the inward visual path is broken.
- Controlled live stimulus → action → consequence → reward → memory acceptance is still unproven.
- Memory persistence/retrieval and organ failure/recovery remain release blockers.

### Immediate execution order
1. **Step 5 — Closed-loop acceptance:** prove one controlled visual/audio stimulus can travel through attention → motivation → CC → action → consequence → reward → memory, with correlation IDs intact.
2. **Step 6 — Memory:** validate restart persistence, retrieval, consolidation and reward-driven future choice.
3. **Step 7 — Recovery:** validate organ health, bounded queues, stale-PID recovery, clean shutdown and restart without a second kernel.
4. **Step 8 — Performance/endurance:** fix scheduler-aware regression tests, measure CPU/RAM/GPU/storage/latency, then run sustained V1 endurance.
5. **Step 9 — Release:** snapshot, documentation/changelog, full release gate, V1 tag.

### Explicitly not part of the current V1 push
- Physical webcam / multi-camera fusion.
- Major neural expansion.
- Metacognition/self-model.
- Distributed organs.
- Large evolutionary experiments.
- Major repository refactor.

The inward virtual environment is a **V1 perception configuration**, not a new cognition system. It exists to give G.A.I. a controllable digital habitat for self-play while keeping the V1 authority chain unchanged.

## Step 1 — Lock the current V1 shape

What:
Make the existing organism architecture stable enough that we stop moving pieces around.

Systems:
- Kernel
- Nervous System
- Senses
- Shared Attention
- CC-V1
- Action/Motor
- Memory
- Lifecycle
- GUI/phenotype

Done when:
We can point to one clear input -> thought -> action -> consequence path.

## Step 2 — Build proper Needs

What:
Turn the existing homeostasis signals into a small, explicit set of needs.

Systems:
- Homeostasis
- Body state
- Instincts
- Emotion/chemistry

Needs to start with:
Energy, rest, safety, stimulation, social, interaction, exploration, maintenance.

Done when:
Each need can rise, fall and be satisfied, and those changes are observable.

## Step 3 — Build Wants

What:
Create short-lived desired outcomes from active needs and the current situation.

Systems:
- Needs
- Perception
- Attention
- Memory
- Prediction
- Neural/experience signals

Done when:
G.A.I. can have more than one possible want and wants can change as circumstances change.

## Step 4 — Build Motivation

What:
Let competing wants influence which thing matters most right now.

Systems:
- Wants
- Instincts
- Emotion
- Prediction
- Experience learning
- Attention

Done when:
The strongest motivation can change without directly becoming an action command.

## Step 5 — Close the behaviour loop

What:
Make the full chain work reliably.

Systems:
- Senses
- Attention
- Needs
- Wants
- Motivation
- CC
- Action/Motor
- Organs
- Consequence
- Reward
- Memory

Done when:
A visual or audio event can change internal state, produce a choice, cause an action, and change what happens next.

## Step 6 — Make Memory useful

What:
Make experience persist in a way that changes later behaviour.

Systems:
- Short-term memory
- Long-term memory
- Retrieval
- Consolidation
- SSD memory banks
- HDD deep storage

Done when:
A restart does not erase meaningful learned experience.

## Step 7 — Make the body recover

What:
Make the organism survive individual organ/process failures.

Systems:
- Organ health
- Supervisor
- Launcher
- Recovery
- Resource limits

Done when:
A failed organ can recover without rebuilding the whole organism.

## Step 8 — Test the real organism

What:
Run controlled experiments and then a longer unsupervised V1 endurance run.

Systems:
- Laboratory
- Diagnostics
- Trace system
- Performance metrics
- Recovery system

Done when:
We have evidence that the loop is stable over time, not just during demonstrations.

## Step 9 — Finish V1

What:
Freeze the working V1 and document it.

Systems:
Everything above.

Done when:
G.A.I. can perceive, maintain needs, form wants, choose between motivations, act, receive consequences, learn, remember and recover.

## Step 10 — Neural Layer

What:
Only now make the neural substrate structurally elastic.

Systems:
- Neural Fabric
- Experience learning
- Needs/Wants/Motivation
- Memory
- Dream

Order:
Temporary connections -> useful connections -> stable connections -> dormant connections.

Done when:
Experience can change the neural structure and the changes remain bounded.

## Step 11 — Sleep and Dream

What:
Let sleep become the main reorganisation period.

Systems:
- Lifecycle
- Dream
- Neural Fabric
- Memory
- Maintenance

Done when:
Wake gathers experience and sleep reorganises it without Central Consciousness micromanaging maintenance.

## Step 12 — Agency

What:
Build more capable planning and self-directed behaviour on top of the stable organism.

Systems:
- Motivation
- Neural Fabric
- Planning
- Memory
- Tools
- Creative organs

This is where multi-step planning, richer creativity and metacognition belong.

## Parked

Do not work on these until the above is stable:
- Multi-camera fusion
- Distributed organs
- Large neural networks
- Major repository refactor
- Large evolutionary experiments
- Advanced metacognition

## Rules

1. One step at a time.
2. Before a complex step, review its relevant audits/docs.
3. Decide WHAT first.
4. Decide HOW only when we reach that step.
5. Test before moving on.
6. Do not add systems just because they are possible.


## Phase 1 completion — 2026-10-06

**Step 1 — Lock the current V1 shape: COMPLETE.**

The current V1 organism path is locked as:
`Senses → Nervous System → Neural Workspace/Attention → CC-V1 → Action/Motor → Organs → Consequence → Reward → Memory`.

Validation: full agent compile passed; 65 automated tests passed when the known physical-camera pytest probe is excluded; live correlated V1 tracing and neural-fabric attention are operational. Historical development documents remain preserved.

Next execution step: **Step 2 — Build proper Needs.**


## Phase 4 completion — 2026-10-06

**Wants & Motivation — COMPLETE.** Needs now generate bounded short-lived desired outcomes which bias motivation without issuing actions. Motivation remains upstream of CC; CC remains action authority. Phase 2/3/4 regression tests pass and live activation is confirmed.

Next execution step: **Phase 5 — close the full behaviour loop (visual/audio stimulus -> want -> motivation -> CC -> action -> consequence -> reward -> memory).**

## Phase 5 progress — 2026-10-06

**Close the behaviour loop — IN PROGRESS.** The V1 path already records action consequences, prediction error, reward and experience memory. This phase is now tightening the acceptance evidence and making the memory storage boundary explicit.

V1 storage decision: the long-term memory framework remains local and SSD-backed under /mnt/gai/memory. Memory uses a small storage-backend contract so HDD and cloud can be added in a future version without changing cognition or memory semantics. No HDD/cloud activation is part of V1.

Implemented in this phase:
- Local SSD memory-bank backend with manifest and per-memory SHA-256 integrity checks.
- MemoryPipeline storage backend boundary; default remains SSD.
- Regression coverage for storage round-trip/tamper detection and reward-driven action preference.

Remaining acceptance work: run a controlled live stimulus -> attention -> want -> motivation -> CC -> motor -> consequence -> reward -> memory experiment and verify learned reward changes a subsequent live choice.


# V2 ROADMAP — capability expansion

V2 is deliberately downstream of V1. Do not begin major V2 implementation until the V1 release gate has passed.

### V2.0 — Learning
Neural Fabric 2.0, temporal associations, contextual routing, reward/prediction-error propagation, habituation/novelty, forgetting, stronger sleep/dream consolidation and causal neural experiments.

### V2.1 — World
Active perception, deliberate re-observation, persistent object/world representations, spatial awareness, affordances, confidence/uncertainty and grounded perception/action.

### V2.2 — Self
Persistent self-model, capability/limitation model, autobiographical continuity, uncertainty about knowledge, functional affect and learned preferences/habits.

### V2.3 — Agency
Needs/drives/goals/subgoals, bounded multi-step planning, strategy revision, curiosity, exploration and internal hypothesis/experiment loops.

### V2.4 — Body & Tools
Richer digital organs, capability discovery, consistent organ contracts, advanced desktop/toy manipulation, optional multi-camera/spatial sensing and sandboxed environments.

### V2.5 — Creation
Autonomous text, image/SVG/paint, audio/music, coding and simulation with create → inspect → self-critique → revise → reward loops and a persistent portfolio.

### V2.6 — Social
Interaction state, turn-taking, shared goals, collaboration, teaching/being taught and long-term interaction continuity.

### V2.7 — Evolutionary Sandbox
Late-stage sandboxed experiments with neural structures, behaviours and capability combinations, with automated testing, rollback and human-controlled promotion.

### V2 guardrail
The V2 architecture must preserve the V1 organism loop:
**Sense → Attend → Interpret → Remember → Predict → Want → Plan → Act → Consequence → Learn → Sleep → Change.**

No V2 feature may create a hidden competing cognitive loop or give a reasoning model direct hardware control.

Detailed V2 roadmap: `docs/V2_ROADMAP.md`.
