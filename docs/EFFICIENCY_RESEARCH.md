# G.A.I. Efficiency Research

Verified 2026-10-06. G.A.I. means the laptop organism: compute, memory, storage, sensory organs, actuators and power state are one experimental body.

## External lessons

### OpenWorm
OpenWorm's strongest architectural lesson is not to build one giant simulation. It separates the organism into composable subsystems, gives each subsystem validation criteria, and tracks dependencies between phases.

**G.A.I. implementation:** keep organs behind nervous-system interfaces; every organ gets an availability state, test, failure mode and measurable contract. Do not let GUI code invent biological state.

### Neuromorphic systems: Loihi / BrainScaleS
These systems exploit event-driven activity, sparse communication, local state and tight compute/memory placement. Loihi specifically emphasizes that neurons need not compute or communicate when nothing changes; BrainScaleS similarly emphasizes event-based observations and hardware/software co-design.

**G.A.I. implementation:** stop treating every tick as an instruction to recompute everything. Use multi-rate clocks: fast homeostasis, medium-rate sensory sampling, event-triggered cognition, slow memory consolidation. Propagate changes through the nervous system rather than polling every subsystem at the same frequency.

### Numenta / HTM
HTM research emphasizes sparse distributed representations and temporal sequence memory. The useful lesson is streaming input, temporal context and sparse active state rather than repeatedly passing large dense histories to a language model.

**G.A.I. implementation:** compress sensory streams into compact state/features; maintain short temporal context and prediction errors locally; only send a small salient workspace to the expensive reasoning model.

## What this means for the laptop

The laptop is an i7-7500U (2 cores / 4 threads), 16 GB RAM, with a GTX 950M and two 1 TB SSDs. The G.A.I. volume is the 1 TB NVMe mounted at /mnt/gai. The removable-HDD concept remains an external organ; the current simulated HDD is SSD-backed.

### Proposed compute budget

1. Nervous system / homeostasis: CPU, only while a test is running.
2. Fast sensory preprocessing: CPU, lightweight and event-oriented.
3. Local language model: expensive organ, launched only for an organism test or explicitly requested cognitive experiment; never a background daemon.
4. GTX 950M: optional accelerator for experiments that fit its memory. Do not reserve it permanently.
5. SSD: persistent memory/deep storage; compression and append-only memory banks.
6. HDD organ: removable/archive role, not active working memory.
7. Audio: PipeWire hardware graph; microphone is input organ, speaker is output organ.
8. Display: screen is a visual sensory surface; the translucent bubble is phenotype, while opaque output windows are tools/artifacts controlled by the organism.

## Efficiency metrics to add

Every future experiment should report CPU seconds per cognitive cycle, wall-clock sensory-to-action latency, peak/average RAM, GPU memory/utilization when used, audio latency, events processed per second, percentage of ticks causing meaningful state change, bytes written to each memory tier, and power measurements when hardware permits.

The target is not maximum tick rate. The target is minimum computation needed to maintain the organism's behaviour and learning.

## Immediate architecture changes

- Keep G.A.I. test-launched only.
- Keep single-instance kernel locking in production.
- Keep organs lifecycle-aware: disconnected/sleeping organs stop producing work.
- Move toward event-triggered cognition instead of fixed-period language-model calls.
- Add sparse sensory summaries and temporal deltas before the reasoning model.
- Make memory consolidation batch only during dream/scheduled consolidation periods.
- Measure before optimizing: preserve a baseline benchmark for each change.
- Treat failed experiments as recorded results, not hidden errors.
