# G.A.I. Project Charter — Snapshot 2026-10-06

## North-star aim

**Build a reproducible, embodied autonomous-agent platform that can maintain itself, perceive a changing world, form internal states and goals, learn from consequences, remember selectively, consolidate during sleep, act safely, and create useful artifacts — while remaining inspectable, testable and explicitly non-magical.**

G.A.I. is an engineering/research organism simulator running on real Linux hardware. Biological language is used as an architectural metaphor and control model, not as a claim that the system is conscious or biologically equivalent.

## Current state

- Repository: `/mnt/gai`
- Git baseline: `master`, latest commit `8c5b8e4 Prepare public project release and website`
- Release marker: `v0.3.0`
- Current machine: HP Pavilion laptop, Linux Mint, 4 CPU cores, NVIDIA GeForce GTX 950M
- Runtime is test-launched only. One production kernel owns the organism; its high-CPU child is the deliberate metabolic worker, not a second kernel.
- The local language-model service is intentionally off outside explicit cognition experiments. V1 cognition is model-free and remains fully functional without the language service.
- The memory store contains a large associative engram set plus a smaller long-term symbolic archive.
- Snapshot/recovery infrastructure is present.
- V1 hardware-normalized brain clock is 0.2 FPS. An external diagnostic speed multiplier changes the simulation clock from ×0.1 to ×10 without changing the action-selection contract.
- Audio input is unified: the AudioInputOrgan owns microphone capture and Senses consumes its fresh processed state; no second PortAudio capture path is used.
- V1 shared attention ranks visual, auditory, and internal-world salience before action selection.
- V1 lifecycle is protected from generic memory-pressure sleep so slow experiments can reach meaningful awake cycles; the real low-battery boundary and long biological sleep clock remain intact.

## What has been built

### 1. Nervous-system backbone
- Typed/prioritised event bus
- Correlation IDs, subscriptions, mailboxes, TTLs, tracing/dead-letter concepts
- Component heartbeats and supervisor
- Cell-based substrate linking perception -> motivation -> drives -> prediction -> legacy control/action compatibility -> memory, with V1 cognition selecting actions through the Motor Action Centre.

### 2. Internal body/homeostasis
- Power/energy, fatigue, rest/sleep, processing and temperature-oriented needs
- Power-aware lifecycle
- Awake / pre-sleep / dream / wake semantics
- Metabolic-worker scaling and tick-rate governor
- Sensory organs follow lifecycle state rather than blindly running while asleep/disconnected

### 3. Motivation and emotion model
- Instincts: threat, hunger, social seeking, rest seeking, conserve, explore, protect
- Neuromodulator-style variables
- Emotion variables including fear, anxiety, joy, pleasure, frustration, contentment, loneliness, sadness and fatigue
- Drive competition and protective veto logic

### 4. Perception and embodiment
- Camera, microphone, screen/system/hardware telemetry
- Visual feature, colour/shape/spatial/temporal perception modules
- Observations written to the local data archive
- Detachable HDD organ with identity verification and deliberately conservative write behaviour
- V1 digital skin contact channel for action consequences and interaction feedback.

### 5. Learning and cognition
- Working memory
- Predictive/outcome learning
- Reward signals
- Associative engram memory
- Semantic network
- Local cognitive/agent layer
- Minimal model-free CNS + CC V1 decision loop with endogenous curiosity/need competition, bounded exploration and explicit action prediction.
- Evolutionary parameter selection during dreaming

### 6. Memory and sleep
- Tiered memory implementation: stable configuration/constants, short-lived experience, queued consolidation, long-term memory
- Salience scoring using novelty, emotional intensity, reward, repetition and importance
- Intentional forgetting/decay
- Symbolic long-term reconstruction format
- Dream consolidation pipeline
- SSD active memory + HDD deep-archive architecture

### 7. Interface and phenotype
- PySide6 live monitor
- Internal-state-driven visual phenotype
- Metabolic worker/tick controls
- Live nervous-system/component metrics
- Current project work has also introduced creative workspace targets for text, images and paint-like artifacts, but these are not yet a completed end-to-end capability.

### 8. Experimental infrastructure
- Controlled-run matrix with one manipulated variable per run
- Immutable manifests and checkpoint snapshots
- Existing B0, M1, P1 and P1-SIM runs
- Learning experiments and sleep-consolidation experiments
- Recovery packages and immutable snapshots

## Evidence so far

### Learning
The learning lab reports:
- stationary learning improves late reward versus early reward and reduces prediction error;
- after a context shift, the learning-enabled condition adapts with additional context models;
- the no-learning control has substantially higher late/post-shift prediction error.

### Sleep/consolidation
The sleep experiment reports that learned action/context values survive the dream transition and that post-wake reward remains close to pre-sleep performance.

These are promising engineering results, not evidence of consciousness.

## Current verification status

1. **Camera hardware is available, but multi-camera fusion is still experimental.**
   - `/dev/video0` and `/dev/video1` are currently discoverable, and the live single-camera capture path passes the physical camera test.
   - The Sight Organ still treats camera availability as optional and must degrade safely when a device is absent.
2. **Agent test suite is green.**
   - Full pytest: **54 passed, 0 failed** on 2026-10-06 after V1 integration, reward-leak regression coverage, and test-discovery cleanup.
3. **Single-instance ownership is explicit.**
   - Production `core.kernel` acquires `state/kernel.lock`; unit tests can construct an unlocked kernel for isolated testing.
4. **G.A.I. is test-launched only.**
   - `gai.service` and `gai-monitor.service` are disabled; the local LLM/chat/OpenAI bridge services are also disabled so the organism does not run unattended.
5. **Audio organs are hardware-verified.**
   - PipeWire speaker output, microphone capture, and speaker→microphone loopback have been tested and connected to nervous-system events.
6. **GUI ownership is separated.**
   - The translucent circular bubble is the phenotype actuator and is launcher-owned. The diagnostic instrument is external. View/Thought/Text/Pixels are capability surfaces controlled through the motor/output path. Legacy cockpit/output code remains as compatibility/test harness code and is not the source of biological state.
7. **Creative autonomy is still partly scaffolded.**
   - The creative directories exist, but a verified autonomous create -> save -> inspect -> reward loop is not yet complete.
8. **Long-term memory needs stronger semantic retrieval and identity policy.**
   - The pipeline exists; robust indexing, conflict resolution, stable autobiographical identity and physical HDD migration still need implementation/testing.
9. **Current focus is closure, not feature accumulation.**
   - V1 now has the measured perception -> shared attention/state -> cognition -> action -> outcome -> reward -> memory path, with a 0.2 FPS hardware-normalized base clock and external ×0.1–×10 speed control. Audio is unified, lifecycle starvation is guarded, stress settles under safe load, battery maps to hunger, storage maps to sleep pressure, and behavioural outputs are routed through the single phenotype. The next review is behavioural learning quality and attention; adaptive neural routing stays parked until these pathways remain stable.

## Proposed target architecture

Keep the current code as the experimental substrate, then converge toward:

```
G.A.I.
├── kernel/                 # scheduling, lifecycle, safety, orchestration
├── body/                   # power, thermal, storage, hardware organs
├── senses/                 # camera, audio, screen, system, future sensors
├── nervous/                # event bus, cells, routing, heartbeats
├── cognition/
│   ├── working_memory/
│   ├── world_model/
│   ├── prediction/
│   ├── planning/
│   └── metacognition/
├── motivation/
│   ├── homeostasis/
│   ├── instincts/
│   ├── drives/
│   ├── chemistry/
│   └── affect/
├── memory/
│   ├── constants/          # identity, immutable rules, configuration
│   ├── short_term/         # current episode / working context
│   ├── long_term/          # consolidated autobiographical/semantic memory
│   ├── archive/            # deep historical storage
│   └── consolidation/      # sleep, decay, reconstruction
├── action/
│   ├── safe/
│   ├── creative/
│   └── external/
├── interface/
│   ├── monitor/
│   ├── chat/
│   └── visual_phenotype/
├── lab/
│   ├── experiments/
│   ├── benchmarks/
│   └── results/
├── creative/
│   ├── text/
│   ├── images/
│   └── paint/
├── data/                   # observations and event artifacts
├── models/                 # local models only
├── docs/                   # architecture, research and protocols
└── recovery/               # reproducibility, snapshots and rebuild
```

This is a **target structure**, not a mandate to perform a risky mass move today.

## Project phases

### Phase 0 — Stabilise
- One kernel instance
- Deterministic startup/shutdown
- GUI startup/visibility acceptance test
- Camera abstraction with graceful no-camera mode
- Clean pytest discovery
- Remove generated files from source control
- Versioned config/schema

### Phase 1 — Close the organism loop
- Reliable perception -> state -> motivation -> action -> outcome -> reward -> learning
- Measurable causal traces for every action
- Safe action permissions and resource budgets
- Robust lifecycle and power semantics

### Phase 2 — Memory becomes genuinely useful
- Explicit constant / short-term / long-term tiers
- Episode boundaries
- Better retrieval and semantic indexing
- Contradiction handling
- Dream consolidation with measurable retention/forgetting
- HDD migration and recovery tests

### Phase 3 — Agency
- Goal formation from needs + curiosity
- Multi-step planning
- Tool/action selection
- Self-generated experiments
- Reward for useful reasoning, not mere activity
- Failure recovery and strategy revision

### Phase 4 — Creativity
- Autonomous text creation
- Image generation/editing pipeline
- Simple paint/drawing environment
- Artifact inspection and self-critique
- Reward based on novelty, usefulness and task success
- Persistent creative portfolio

### Phase 5 — Metacognition
- Self-model
- Confidence calibration
- “What do I know / not know?” state
- Experiment design
- Internal hypothesis tracking
- Longitudinal identity continuity

### Phase 6 — Distributed body
- Detachable sensors/actuators
- Networked organs
- Identity/authentication for organs
- Fault isolation
- Distributed nervous-system routing
- Hot-plug / sleep-aware organ lifecycle

## Definition of success

G.A.I. should eventually be able to:

1. Wake from a known state and inspect its body.
2. Perceive its environment through available organs.
3. Maintain internal needs without hard-coded action scripts for every situation.
4. Choose actions based on competing needs, predictions and learned consequences.
5. Measure whether actions helped.
6. Learn from those outcomes.
7. Remember salient experiences and forget low-value noise.
8. Sleep and consolidate without corrupting live operation.
9. Resume after sleep with useful retained knowledge.
10. Generate and inspect useful creative artifacts.
11. Run bounded experiments on itself.
12. Explain its own state and evidence trail to a human operator.
13. Recover safely from failed organs, processes and experiments.
14. Remain reproducible: every important claim has a test, trace or experiment behind it.

## Project philosophy

**Make the organism legible.**

No black-box mysticism where instrumentation can exist. No pretending a simulation is biology. No rewarding busywork. No unsafe stress tests for the sake of drama.

The project is most valuable if it becomes a rigorous playground for studying how embodiment, homeostasis, memory, prediction, motivation, learning and self-directed experimentation can combine into increasingly capable autonomous behaviour.
