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

## Current baseline — verified 2026-10-07
- [x] One production kernel instance is protected by `state/kernel.lock`; the high-CPU child visible as `main.py` is the intentional metabolic worker, not a second kernel.
- [x] Architecture clarified: the Bubble is an output organ, not the G.A.I. runtime/container; the runtime must remain independent of visual output.
- [x] Screen-only sensory regression: `test_senses.py` passes after the V1 inward-vision change.
- [ ] Full regression suite: two legacy kernel tests still assume cognition completes inside one tick; these need scheduler-aware assertions before release.
- [x] G.A.I. is test-launched only; unattended organism/monitor/model services remain disabled.
- [x] Restore the translucent circular phenotype bubble as part of the test launcher; diagnostic remains an external observer.
- [x] Audio input/output organs are connected and hardware-tested.
- [x] V1 outward webcam path is disabled and archived; the persistent screen stream is now the sole visual input for inward virtual perception.
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
- [x] Persistent visual stream: the screen is the sole V1 visual stream; CNS selects an inward virtual field without screenshot-triggered cognition.
- [x] Display guard: the organism maintains no-idle/no-lock/no-suspend session policy while running.
- [x] Invisible focus organ: separate gaze target follows CNS focus and feeds phenotype pupil/proximity response; V1 focus defaults to the inward virtual habitat.
- [x] Speaker organ has a bounded V1 speech path plus non-verbal affective tone fallback; completion/failure is stateful and correlated.
- [x] First neural fabric layer: sparse sensory-attention-action routes learn from consequences and become more plastic during pre-sleep/dream maintenance.
- [ ] Neural layer: expand adaptive routing beyond the sparse V1 substrate while preserving bounded resource use.
- [x] V1 lifecycle guard: generic memory-pressure sleep is disabled for V1; the slow biological sleep clock and real low-battery protection remain.
- [ ] Local language cognition is currently unavailable because the model service is intentionally off; run it only as an explicit bounded cognition experiment.
- [x] Multi-agent Agent Gateway exists outside cognition, with per-agent/session identity, correlation IDs, permissions and serialized requests through the V1 user-command boundary.
- [x] Inward-vision change materially reduced live PerceptionCell cost from ~77.6 ms/call to ~38.8 ms/call in the observed runtime.

## Priority 1 — finish the closed organism loop
- [x] Build one shared cross-modal Attention System for sight, hearing, memory and internal imagery.
- [x] Drive V1 attention from cross-modal salience + curiosity + prediction/state rather than a fixed/default focus.
- [ ] Add attention dwell/saccade history so attended sensory patches become traceable experiences.
- [x] V1 nervous clock targets 20 Hz; central cognition is bounded to its own cadence so CC work cannot monopolise every nervous tick.
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

## External multi-agent integration — IMPLEMENTED
- [x] Build a loopback-only Agent Gateway for multiple external ChatGPT/agent sessions.
- [x] Isolate chat history by agent/session and preserve correlation IDs.
- [x] Serialize external command requests through the existing V1 user-command boundary.
- [x] Deny unknown agents and reject commands outside the V1 command allowlist.
- [x] Keep the gateway external to CC-V1, Motor and organ authority; document the contract in docs/AGENT_GATEWAY_2026-10-07.md.

## V1 inward-vision decision
- [x] Physical webcam module/test archived rather than deleted.
- [x] `visual_mode: inward_virtual` and `camera: false` are authoritative in V1 config.
- [x] Screen stream is fresh and consumed as `mode: in` by the live sight path.
- [x] Viewfinder is screen-only in V1.
- [x] Snapshot `snapshots/gai-inward-vision-20261007.tar.gz` created and checksummed.

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
- [x] Freeze the current V1 interfaces: Senses → Nervous System → Global Workspace → CC-V1 → Action/Motor → Organs → Consequence → Reward → Memory.
- [x] Clarify the architectural role of the Bubble: it is an output organ, while the G.A.I. runtime remains independent of its presence.
- [x] Lock schemas for visual input, audio input, CC workspace, intention, motor command, speech request, speech result, reward and memory event.
- [x] Remove or disable competing legacy paths rather than letting them silently coexist.
- [x] Make every organ expose one clear input/output contract and health state.
- [x] Snapshot the current working tree before cleanup.
- [x] Produce one V1 architecture diagram and treat it as the contract for release.

## Gate 1 — input organs: prove the body can hear and see
### Vision
- [x] Persistent desktop stream runs continuously without screenshot-triggered cognition.
- [x] V1 outward webcam path is disabled; the persistent screen stream is the sole visual input.
- [x] Inward virtual visual mode is authoritative for V1 and defaults attention to the virtual habitat/screen.
- [ ] Focus bubble is the invisible attention target; the eye follows the same focus state.
- [ ] Proximity/focus affects phenotype pupil response.
- [ ] Sight Organ produces a bounded perceptual representation: attended detail + compressed periphery + temporal change.
- [x] The screen visual source is represented in state and traceable in the CC sensory workspace.
- [x] The optional physical-camera test/module is archived out of the V1 runtime; screen-only sensory coverage remains in `agent/tests/test_senses.py`.
- [ ] Add an end-to-end vision test: source → sight organ → attention → CC workspace.

### Audio
- [ ] PipeWire microphone capture is the single authoritative audio input path.
- [ ] Auditory Organ produces signal level, transient, attended region/frequency and novelty.
- [ ] Audio attention can beat visual attention when its salience is higher.
- [ ] Audio events enter the same Global Workspace as visual events.
- [ ] Add an end-to-end audio test: microphone → auditory organ → attention → CC workspace.

## Gate 2 — output organs: prove G.A.I. can answer the world
### Output-organ architecture
- [ ] Formalise a common `OutputOrgan` interface for all expressive/action outputs.
- [ ] Keep the Bubble classified as an output organ; it must not own or contain the G.A.I. runtime.
- [ ] Define the neural/CC → output-organ data contract.
- [ ] Separate output-organ startup/shutdown/recovery from the kernel lifecycle.
- [ ] Add output-organ health/capability state to Diagnostic Instruments.
- [ ] Prove the kernel remains alive when the Bubble/output organ is stopped or unavailable.
- [ ] Prove an output organ can reconnect to an already-running kernel.

### Speech
- [x] Speaker/output organ has one authoritative request boundary.
- [x] CC can submit a speech intention without directly touching audio hardware.
- [x] Speech request → synthesis → playback → completion/failure is statefully traced and correlated.
- [x] Playback failure produces a structured consequence rather than a silent error.
- [x] Visible speech/phenotype output and audible output share the same CC intention.
- [x] Test short speech, repeated speech, interruption and unavailable-output recovery paths.
- [x] Replace the current non-verbal-only speaker limitation with a bounded V1 speech path.

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
- [x] Physical webcam is intentionally out of V1; the camera module/test is archived and the deterministic screen-only sensory contract passes.
- [ ] Microphone input is live and traceable.
- [x] V1 visual input is live and traceable through the inward screen stream.
- [ ] Screen-input → attention → CC end-to-end acceptance is still required.
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

**Next:** Phase 5 — controlled closed-loop acceptance: stimulus -> attention -> want -> motivation -> CC -> action -> consequence -> reward -> memory.

## Phase 5 — Close the behaviour loop: IN PROGRESS — 2026-10-07
- [x] Keep the full V1 chain explicit: stimulus -> neural attention -> want -> motivation -> CC -> motor -> consequence.
- [x] Feed measured consequences back into prediction error and reward.
- [x] Learn action preferences from reward so consequences can change future choices.
- [x] Persist closed-loop experiences into short-term memory and the sleep consolidation queue.
- [x] Add the V1 SSD memory-bank abstraction with checksum/manifest and future HDD/cloud backend slots.
- [x] Add regression tests for SSD memory-bank round-trip, tamper detection and reward-driven preference change.
- [ ] Prove the complete live stimulus -> action -> consequence -> reward -> memory trace in a controlled experiment.
- [ ] Validate that learned reward changes a subsequent live CC choice under the same context.

**Next:** controlled closed-loop acceptance experiment, then Phase 5 completion. Inward virtual vision is now the V1 visual configuration for this experiment.


## Internal State → Affect Validation
- [ ] Audit the live internal-state variables: energy, fatigue, curiosity, boredom, stress, satisfaction and confidence, including their sources and update rates.
- [ ] Define measurable physiological/functional signals that legitimately influence each state; do not infer emotion from CPU load or temperature alone.
- [ ] Build an affect/state estimator that combines homeostatic state, prediction error, reward, novelty, attention and recent consequences.
- [ ] Map internal-state combinations to bounded functional affect labels/phenotypes without treating labels as literal subjective feelings.
- [ ] Verify that affect/state changes alter attention, motivation, CC choices and output behaviour through the existing V1 loop.
- [ ] Add controlled experiments: stimulus → internal-state change → behaviour → consequence → reward → state update.
- [ ] Add hysteresis/decay so transient sensor noise does not cause emotional thrashing.
- [ ] Expose a compact internal-state trace to the external Diagnostic Instrument for observation only.
- [ ] Add acceptance tests proving that the same external stimulus can produce different behaviour when internal state differs.
- [ ] Distinguish hardware health telemetry from organism affect: CPU/GPU temperature/load are body signals, not emotions by themselves.
- [ ] After V1 closed-loop acceptance, integrate validated affect into the Neural Fabric/CC without creating a competing control loop.

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
