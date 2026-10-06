# G.A.I. Phase 5 — Close the Behaviour Loop

Date: 2026-10-06
Status: IMPLEMENTED — CONTROLLED LIVE ACCEPTANCE REMAINS

## Goal
Close the biological loop:

stimulus → neural attention → want → motivation → CC → motor → consequence → reward → memory → future choice

## What is already live
- Neural Fabric owns V1 attention selection.
- Wants are derived from needs and context and bias motivation without issuing commands.
- CC-V1 remains action authority.
- Motor reports structured action completion/consequence events.
- Prediction measures observed body-state change and produces prediction error.
- Reward is derived from measured consequence rather than a self-reported success flag alone.
- ExperiencePolicy learns action preferences from reward.
- Experiences enter short-term memory and the MemoryPipeline sleep queue.
- Sleep consolidation commits salient symbolic memories to persistent storage.

## V1 storage boundary
G.A.I. now has a small pluggable storage contract.

Current backend: LocalSSDBackend → /mnt/gai/memory/banks/long_term

The backend writes a manifest and SHA-256 checksum for each memory entry. The interface deliberately leaves future backends open for:
- detachable HDD
- cloud/object storage

Those backends are placeholders only. V1 does not activate them.

## Tests added
- SSD backend manifest identifies the active backend and future expansion points.
- Memory-bank write/read round trip works.
- Tampered memory-bank payloads fail checksum validation.
- MemoryPipeline can consolidate through the storage boundary.
- Positive reward increases a future action preference.
- Negative consequence decreases a future action preference.

## Acceptance gate still open
Run one controlled live experiment and capture a correlated trace proving:
1. stimulus changes attention;
2. attention/context changes the active want;
3. motivation/CC changes the selected action;
4. motor produces a consequence;
5. consequence changes prediction error/reward;
6. the experience is stored;
7. the learned reward changes a later choice under the same context.

No cloud/HDD expansion is required for V1.