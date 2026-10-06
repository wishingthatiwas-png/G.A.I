# G.A.I. Phase 2 — Needs & Motivation

## Current status

**FOUNDATION IMPLEMENTED — LIVE ACTIVATION PENDING RESTART**

The V1 architecture remains locked. Phase 2 now has explicit homeostatic needs and motivation pressure rather than relying only on generic curiosity/state variables.

## Implemented

- Energy / power pressure
- Rest / sleep pressure
- Safety / threat pressure and instinct veto
- Social pressure
- Stimulation / exploration pressure
- Maintenance pressure from compute/storage conditions
- Chemistry and emotion continue to translate body state into affect
- V1 CC action scoring now accepts motivation pressure as a bias while CC remains the action authority
- Phase 2 regression tests: **3/3 PASS**

## Intended causal loop

`Body state → Needs → Instinct → Chemistry/Emotion → Neural salience → CC action choice → Outcome → Reward → Needs`

## Important boundary

Needs do not directly execute actions. They bias salience and decision scoring; emergency safety instincts may veto unsafe cognition.

## Remaining Phase 2 gate

Restart the live organism with the new modules and demonstrate that changing need state changes live CC action selection. The current running process predates this patch, so no claim of live activation is made yet.
