# G.A.I. V1 Backend Lockdown

Date: 2026-10-07
Status: **FROZEN**

## Purpose

This document freezes the backend shape of G.A.I. V1. The project is now in reliability/release mode rather than architecture-expansion mode.

## Canonical path

**Senses → Nervous System → Neural Workspace / Attention → CC-V1 → Action / Motor → Organs → Consequence → Reward → Memory**

## Authority

- Kernel owns lifecycle and the single production lock.
- Neural Fabric owns V1 attention.
- CC-V1 owns high-level intention.
- Motor Action Centre owns execution.
- Organs perform I/O and report health/outcomes.
- Memory persists experience; it does not execute.
- Diagnostics remain external.
- Capability/toy applications remain external tools.

## Backend guard state

- `v1_mode=true`
- `central_cognition_v1=true`
- alternate autonomous cognition disabled
- V1 background motor exploration disabled
- unattended organism/model services disabled

## What may change

Only changes required for:
- correctness and bug fixes
- contract/schema hardening
- tests
- observability/diagnostics
- failure recovery
- resource limits/performance
- release documentation

## What is frozen

No new major organs, alternate cognition paths, large neural expansion, metacognition, evolutionary systems, or major repository refactors during V1 acceptance.

## Release blockers

1. CC ↔ sensory/output closed-loop proof.
2. Organ health and stale-PID recovery. Persistent-organ startup now validates PID liveness, zombie state and expected command path; remaining health work is endurance/recovery validation.
3. Memory persistence/retrieval validation.
4. Performance/endurance validation.
5. Final V1 release gate.

Speech output is no longer a backend blocker: the bounded speech path now has a single request boundary, playback completion/failure state, and correlation IDs.

## Rule

If a proposed change alters the canonical path or authority ownership, stop and update the architecture contract before implementing it.
