# G.A.I. TODO — current path

## Latest documentation
- [x] Development-document preservation policy saved in `docs/DOCUMENT_PRESERVATION_POLICY_2026-10-06.md`; documentation is archive/version-only, never delete/replace historical project data.
- [x] Simple build plan saved in `docs/MASTER_BUILD_PLAN_2026-10-06.md`; this is the current execution order.
- [x] GUI/visual/neural implementation audit saved in `docs/AUDIT_2026-10-06_GUI_NEURAL.md`.
- [x] Neural-layer roadmap saved in `docs/NEURAL_LAYER_ROADMAP.md`; Phase 2 is the next neural implementation target.
- [x] Needs/wants/motivation roadmap saved in `docs/MOTIVATION_WANTS_NEEDS_ROADMAP.md`.
- [ ] Formalise explicit need objects with deficits, targets, urgency, rates and satisfaction channels.
- [ ] Build an emergent want generator from needs, context, attention, prediction and learned experience.
- [ ] Build motivation arbitration so competing wants influence attention/action without becoming direct commands.
- [ ] Connect want satisfaction and failure to ExperiencePolicy and NeuralFabric learning, with sleep/dream maintenance below CC level.

## Current baseline — verified 2026-10-06
- [x] One production kernel instance is protected by `state/kernel.lock`; the high-CPU child visible as `main.py` is the intentional metabolic worker, not a second kernel.
- [x] Software regression suite: **65 passed, 0 failed** with the standalone physical-camera probe excluded; the full suite is **65 passed, 1 known hardware-test failure** because `test_camera` cannot open `/dev/video0` in the pytest process, while the live camera organ captures successfully.
- [x] G.A.I. is test-launched only; unattended organism/monitor/model services remain disabled.
- [x] Restore the translucent circular phenotype bubble as part of the test launcher; diagnostic remains an external observer.
- [x] Audio input/output organs are connected and hardware-tested.
- [x] Live camera capture is working on the physical laptop; multi-camera end-to-end use is still unverified.
- [x] Sight Organ: visual-field stitching, foveal focus, peripheral compression, exposure/colour adaptation and source discovery.
- [x] Auditory Organ: coarse unattended bands plus detailed attended acoustic region.
- [x] Motor/Action Centre owns physical movement and output/tool intentions; GUI is the actuator.
- [x] Proprioception closes the loop between motor commands and bubble position.
- [x] Simulated SSD-backed deep-storage organ exists for safe testing.
- [x] Snapshot/recovery infrastructure exists.
- [x] Digital skin/body interface: V1 contact schema is live and interaction outcomes feed back through the body/nervous-system path.
- [x] Audio input unified: Senses consumes the live AudioInputOrgan/PipeWire stream instead of opening a second PortAudio capture path.
- [x] Shared attention: V1 uses one salience field across visual events, motion, auditory transients, audiovisual synchrony, habituation and internal world targets.
- [x] Experience/emergence framework: action preferences learn from consequences online, sensory habituation reduces repeated stimulus salience, and causal rewards are kept separate from prior-action prediction rewards.
- [x] Phenotype cleanup: one emotion/attention/action-driven bubble; legacy GUI duplicates archived.
- [x] Persistent toy suite: View, State/Thought, Text and Pixels live in one external application and are controlled through G.A.I.'s output organ.
- [x] Persistent visual stream: camera and desktop are rolling sensory streams; CNS selects the active visual source rather than triggering screenshot captures.
- [x] Display guard: the organism maintains no-idle/no-lock/no-suspend session policy while running.
- [x] Invisible focus organ: separate gaze target follows CNS focus and feeds phenotype pupil/proximity response; camera attention has a dedicated lens indicator.
- [x] Speaker organ is non-verbal/affective only; no speech synthesis path.
- [x] First neural fabric layer: sparse sensory-attention-action routes learn from consequences and become more plastic during pre-sleep/dream maintenance.
- [ ] Neural layer: expand adaptive routing beyond the sparse V1 substrate while preserving bounded resource use.
- [x] V1 lifecycle guard: generic memory-pressure sleep is disabled for V1; the slow biological sleep clock and real low-battery protection remain.
- [ ] Local language cognition is currently unavailable because the model service is intentionally off; run it only as an explicit bounded cognition experiment.

## Priority 1 — finish the closed organism loop
- [x] Build one shared cross-modal Attention System for sight, hearing, memory and internal imagery.
- [x] Drive V1 attention from cross-modal salience + curiosity + prediction/state rather than a fixed/default focus.
- [ ] Add attention dwell/saccade history so attended sensory patches become traceable experiences.
- [x] V1 cognition no longer uses a competing periodic fallback; one kernel tick is one CNS/CC decision opportunity, with the current hardware-normalized base clock at 1.5 FPS and an external ×0.1–×10 speed multiplier.
- [ ] Add sparse temporal sensory summaries/deltas before the language model.
- [ ] Add a single efficiency benchmark: CPU seconds/thought, sensory→action latency, RAM, GPU use when present, event rate, meaningful-tick ratio and storage writes.
- [ ] Tune the local model so cognitive cycles do not starve the rest of the organism on this laptop.
- [x] Causal trace for the V1 cycle is implemented and correlated across perception → attention/state → cognition → motor action → outcome → reward → memory.

## Priority 2 — make memory genuinely useful
- [ ] Formalise the three live memory tiers: constants/identity, short-term episode/working context, long-term consolidated memory.
- [ ] Add robust semantic retrieval and conflict/contradiction handling.
- [ ] Add episode boundaries and autobiographical identity continuity.
- [ ] Validate sleep consolidation with retention + forgetting measurements.
- [ ] Build SSD memory-bank creation/rotation/compaction with checksums and manifests.
- [ ] Complete the real detachable-HDD docking lifecycle: detect → verify → online → archive → safe detach → offline.
- [ ] Test recovery from a missing, replaced or corrupted deep-memory organ.

## Priority 3 — agency and useful action
- [ ] Make goal formation emerge from needs, curiosity, prediction and task relevance.
- [ ] Add bounded multi-step planning with explicit action/resource budgets.
- [ ] Add failure recovery and strategy revision rather than immediately retrying the same action.
- [ ] Reward useful reasoning and successful outcomes, not raw thought count or activity.

## Priority 4 — creative organs
- [ ] Complete autonomous create → save → inspect → self-critique → reward for text.
- [ ] Complete the same loop for SVG/image and paint artifacts.
- [ ] Keep a persistent creative portfolio with provenance.
- [ ] Make the toy/organ interface consistent: View, Thought, Text and Pixels are capabilities, not competing control systems.

## Parked until the core loop is solid
- [ ] Physical multi-camera fusion beyond source discovery.
- [ ] Distributed/networked body and hot-pluggable remote organs.
- [ ] Full metacognition/self-model.
- [ ] Large evolutionary experiments and additional simulated chemistry.
- [ ] Any major mass refactor of the repository layout.

## Rules for the next experiments
- One manipulated variable per experiment.
- Snapshot before risky changes.
- Keep diagnostics external to the organism.
- No automatic background services.
- Every meaningful claim gets a test, trace or experiment result.
- Prefer less computation that produces better behaviour over higher tick rates.

## Behaviour / Phenotype Wave
- [x] Rebalance V1 threat: CPU load is normalized by core count; ordinary load is not treated as danger.
- [x] Lower stress accumulation and allow cortisol/arousal to settle naturally.
- [x] Keep curiosity/exploration active when energy and battery are healthy.
- [x] Treat successful contact as a social/homeostatic reset.
- [x] Add safe non-verbal vocalization as an action/output channel.
- [x] Integrate speech output into the single G.A.I. bubble, revealing three characters at a time.
- [x] Stop auto-launching the Toys application; toys remain optional external capability apps.
- [x] Keep diagnostics external and observational rather than part of the organism phenotype.
- [x] Make launcher shutdown PID-based so a running kernel cannot survive a normal stop because of a command-pattern mismatch.
- [x] Give G.A.I. one eye in the single phenotype bubble; eye focus remains driven by the sight/attention state.
- [ ] Add adaptive neural routing/fabric only after behaviour is stable; measure route usefulness before adding dynamic connections.
- [x] Behavioural connectivity audit: repaired vocalize intention validation, shared V1 world/contact state, speech-output persistence, and rest-debt discharge.
- [x] Validate vocalization/speech during a sustained behavioural run; vocalize intention, motor submission and visible speech output were observed on the fresh kernel.

# V1 LOCKDOWN PLAN — backend first
## Mission
**Do not add major new organs until the backend is boringly reliable.**
V1 is complete when G.A.I. can continuously receive sensory input, route it through the nervous system and CC, speak/act through the output organs, learn from consequences, persist the resulting experience, recover cleanly, and run for a sustained period without supervision.

## Gate 0 — freeze the architecture
- [ ] Freeze the current V1 interfaces: Senses → Nervous System → Global Workspace → CC-V1 → Action/Motor → Organs → Consequence → Reward → Memory.
- [ ] Lock schemas for visual input, audio input, CC workspace, intention, motor command, speech request, speech result, reward and memory event.
- [ ] Remove or disable competing legacy paths rather than letting them silently coexist.
- [ ] Make every organ expose one clear input/output contract and health state.
- [ ] Snapshot the current working tree before cleanup.
- [ ] Produce one V1 architecture diagram and treat it as the contract for release.

## Gate 1 — input organs: prove the body can hear and see
### Vision
- [ ] Persistent desktop stream runs continuously without screenshot-triggered cognition.
- [ ] Persistent camera stream runs continuously and can be selected as the active visual source.
- [ ] in/out visual mode switches correctly.
- [ ] Focus bubble is the invisible attention target; the eye follows the same focus state.
- [ ] Proximity/focus affects phenotype pupil response.
- [ ] Sight Organ produces a bounded perceptual representation: attended detail + compressed periphery + temporal change.
- [ ] Camera/desktop source selection is represented in state and traceable in CC input.
- [ ] Fix the remaining physical-camera pytest failure without weakening the live hardware test.
- [ ] Add an end-to-end vision test: source → sight organ → attention → CC workspace.

### Audio
- [ ] PipeWire microphone capture is the single authoritative audio input path.
- [ ] Auditory Organ produces signal level, transient, attended region/frequency and novelty.
- [ ] Audio attention can beat visual attention when its salience is higher.
- [ ] Audio events enter the same Global Workspace as visual events.
- [ ] Add an end-to-end audio test: microphone → auditory organ → attention → CC workspace.

## Gate 2 — output organs: prove G.A.I. can answer the world
### Speech
- [ ] Speaker/output organ has one authoritative request queue.
- [ ] CC can submit a speech intention without directly touching audio hardware.
- [ ] Speech request → synthesis → playback → completion/failure is fully traced.
- [ ] Playback failure produces a structured consequence rather than a silent error.
- [ ] Visible speech/phenotype output and audible output share the same CC intention.
- [ ] Test short speech, repeated speech, interruption and unavailable-output recovery.
- [ ] Replace the current non-verbal-only speaker limitation with a bounded V1 speech path.

### Action
- [ ] CC intentions pass through one validated Action/Motor boundary.
- [ ] Physical movement, GUI movement and toy/capability actions use the same intention → motor contract.
- [ ] Proprioception reports the actual result back to the nervous system.
- [ ] Invalid/unsafe intentions are rejected and recorded as consequences.
- [ ] Test successful action, failed action and unavailable actuator.

## Gate 3 — CC ↔ both input and output
**This is the main V1 milestone.**
- [ ] CC receives a compact multimodal workspace containing sight + hearing + body state + relevant memory.
- [ ] CC can identify what it is attending to and why.
- [ ] CC produces structured intention/prediction/confidence, never raw hardware commands.
- [ ] CC can choose look/listen/move/interact/vocalize/rest/wait through the action boundary.
- [ ] CC can speak in response to sensory input.
- [ ] CC can hear its own output as an audio event without creating an uncontrolled feedback loop.
- [ ] CC can visually respond to what it sees.
- [ ] Run a closed-loop test: stimulus → attention → CC thought → speech/action → sensory consequence → CC update.
- [ ] Correlation IDs must survive the entire loop.
- [ ] No sensor bypasses CC and no actuator bypasses the action boundary.

## Gate 4 — learning, memory and continuity
- [ ] Formalise constants/identity, short-term working/episode memory and long-term consolidated memory.
- [ ] Store meaningful sensory → thought → action → outcome episodes rather than raw noise.
- [ ] Add semantic retrieval and contradiction handling.
- [ ] Add episode boundaries and autobiographical continuity.
- [ ] Validate that reward changes future action preference rather than merely changing displayed emotion.
- [ ] Validate habituation: repeated unimportant input becomes cheaper/less salient.
- [ ] Validate novelty: genuinely new input can interrupt the current focus.
- [ ] Validate sleep consolidation with a retention/forgetting experiment.
- [ ] Implement SSD memory-bank creation, manifest, checksum, rotation and compaction.
- [ ] Complete detachable-HDD detect → verify → online → archive → safe detach → recovery tests.

## Gate 5 — robustness and recovery
- [ ] Add organ health states: healthy / degraded / unavailable / recovering.
- [ ] Every input/output organ must fail gracefully without taking down the kernel.
- [ ] CC must receive explicit unavailable/degraded capability state.
- [ ] Add restart/recovery tests for camera, microphone, speaker, GUI and memory organ.
- [ ] Confirm exactly one kernel instance after every launch/restart scenario.
- [ ] Confirm clean shutdown leaves no orphaned sensory/output processes.
- [ ] Confirm stale PID/state recovery.
- [ ] Add bounded queues/backpressure so slow speech/model calls cannot starve perception.
- [ ] Add CPU/RAM/storage-write limits and measure them on the old laptop.

## Gate 6 — CC performance and local model boundary
- [ ] Benchmark sensory → CC latency, CC → action latency, CPU seconds/thought, RAM, storage writes and meaningful ticks.
- [ ] Tune the local model so cognition cannot starve sensory and motor organs.
- [ ] Enforce a hard cognition timeout and structured fallback when the model is unavailable/slow.
- [ ] Keep the model outside the organism hardware boundary: model reasons; CC validates; Action Centre executes.
- [ ] Run a sustained local-model test rather than a short probe.
- [ ] Record model latency and failures as first-class experimental data.

## Gate 7 — V1 endurance test
- [ ] Snapshot before endurance run.
- [ ] Start G.A.I. with no manual intervention.
- [ ] Feed it controlled visual and audio stimuli.
- [ ] Require it to attend, think, speak and act.
- [ ] Verify consequences return to CC.
- [ ] Verify memory persists across cycles.
- [ ] Verify attention changes when stimulus salience changes.
- [ ] Verify output failure does not crash cognition.
- [ ] Verify input failure does not crash cognition.
- [ ] Run long enough to expose leaks, queue growth, runaway reward and memory spam.
- [ ] Capture a complete trace and automated health report.
- [ ] Repeat after restart and confirm continuity/recovery.

## V1 RELEASE GATE — all must be true
- [ ] Full automated test suite is green on the supported laptop configuration.
- [ ] Physical camera test is green, or replaced by a deterministic hardware-contract test plus a separately passing live hardware probe.
- [ ] Microphone input is live and traceable.
- [ ] Camera input is live and traceable.
- [ ] Screen input is live and traceable.
- [ ] Speech output is live and traceable.
- [ ] Motor/GUI output is live and traceable.
- [ ] CC communicates with both sensory input and output organs through the same closed loop.
- [ ] Memory survives restart.
- [ ] Organ failures are recoverable.
- [ ] No competing kernel/legacy autonomous loop is active.
- [ ] Performance is within the laptop resource budget.
- [ ] Endurance run passes.
- [ ] Snapshot/archive is created.
- [ ] V1 changelog and architecture contract are written.
- [ ] Tag the release as G.A.I. V1.

## Explicitly V2 — do not let these derail lockdown
- [ ] Adaptive neural fabric beyond the current bounded substrate.
- [ ] Full metacognition/self-model.
- [ ] Physical multi-camera fusion beyond the V1 source contract.
- [ ] Distributed/networked organs.
- [ ] Large evolutionary/chemistry experiments.
- [ ] Major repository refactor.
- [ ] Advanced autonomous creative portfolio.
- [ ] Anything that does not make the closed input → CC → output loop more reliable.

## V1 definition of done
**G.A.I. can see, hear, think, speak, act, feel the consequence, learn from it, remember it, and recover when one of those organs fails — without a second hidden control loop doing the real work.**


# PHASE STATUS — 2026-10-06

## Phase 1 — V1 Shape Lock: COMPLETE
- [x] Snapshot `gai-V1-0.75-20261006-224023.tar.gz` created and checksummed.
- [x] V1 input → neural/attention → CC → action → consequence → reward → memory path locked.
- [x] Neural Fabric is the V1 attention authority; CC is not a competing attention controller.
- [x] Diagnostic remains external to the organism.
- [x] Agent tree compiles cleanly.
- [x] Regression suite passes 65/65 when the known physical-camera pytest probe is excluded.
- [x] Lifecycle wake recovery boundary is explicit.
- [x] Historical development documents preserved; no destructive document cleanup performed.

**Next:** Phase 2 / Step 2 — explicit Needs.


## Phase 4 — Wants & Motivation: COMPLETE
- [x] Explicit short-lived wants derived from needs and context.
- [x] Wants influence motivation scores without becoming action commands.
- [x] Active wants exposed in runtime motivation snapshot.
- [x] Phase 4 regression tests pass.
- [x] Restart and validate live want/action influence.

**Next:** Phase 5 — close the live behaviour loop: stimulus -> attention -> want -> motivation -> CC -> action -> consequence -> reward -> memory.

## Phase 5 — Close the behaviour loop: IN PROGRESS
- [x] Keep the full V1 chain explicit: stimulus -> neural attention -> want -> motivation -> CC -> motor -> consequence.
- [x] Feed measured consequences back into prediction error and reward.
- [x] Learn action preferences from reward so consequences can change future choices.
- [x] Persist closed-loop experiences into short-term memory and the sleep consolidation queue.
- [x] Add the V1 SSD memory-bank abstraction with checksum/manifest and future HDD/cloud backend slots.
- [x] Add regression tests for SSD memory-bank round-trip, tamper detection and reward-driven preference change.
- [ ] Prove the complete live stimulus -> action -> consequence -> reward -> memory trace in a controlled experiment.
- [ ] Validate that learned reward changes a subsequent live CC choice under the same context.

**Next:** controlled closed-loop acceptance experiment, then Phase 5 completion.


# V2 ROADMAP — parked until V1 release

V2 is the capability expansion layer. V1 lockdown remains the active execution priority.

- [ ] V2.0 Learning — richer sparse Neural Fabric, temporal/contextual learning, novelty, forgetting, causal neural experiments.
- [ ] V2.1 World — active perception, re-observation, persistent world/object model, spatial awareness and grounding.
- [ ] V2.2 Self — persistent self-model, autobiographical continuity, capability model, uncertainty and functional affect.
- [ ] V2.3 Agency — drives/goals, bounded multi-step planning, strategy revision, curiosity and internal experiments.
- [ ] V2.4 Body & Tools — richer organs, capability discovery, tool/environment interfaces and optional multi-camera/spatial sensing.
- [ ] V2.5 Creation — autonomous text/image/audio/code/simulation projects and persistent creative portfolio.
- [ ] V2.6 Social — interaction state, collaboration, teaching/being taught and continuity.
- [ ] V2.7 Evolutionary Sandbox — safe experimental self-modification with testing, rollback and human-controlled promotion.

V2 guardrail: preserve the V1 loop and never introduce hidden competing control paths. Detailed roadmap: `docs/V2_ROADMAP.md`.
