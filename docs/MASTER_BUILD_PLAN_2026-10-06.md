# G.A.I. Simple Build Plan — 2026-10-06

This is the current execution plan.

Detailed implementation HOW belongs in the step's working session.
Audit documents record what has already been tested and should be consulted before changing an area.

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

**Wants & Motivation — IMPLEMENTED.** Needs now generate bounded short-lived desired outcomes which bias motivation without issuing actions. Motivation remains upstream of CC; CC remains action authority. Phase 2/3/4 regression tests pass.

Next execution step: **Live activation and then close the full behaviour loop (visual/audio stimulus -> want -> motivation -> CC -> action -> consequence -> reward).**
