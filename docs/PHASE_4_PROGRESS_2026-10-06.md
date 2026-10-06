# G.A.I. Phase 4 — Wants & Motivation
Date: 2026-10-06

## Status
**IMPLEMENTED — TESTED — LIVE ACTIVATION NEXT**

Phase 4 turns explicit needs into short-lived desired outcomes ("wants") and lets those wants influence motivation without becoming direct action commands.

## Architecture
Needs -> Wants -> Motivation -> Neural salience/CC -> Action boundary

Wants are bounded, inspectable objects containing:
- desired outcome
- strength
- target
- action affinity
- reason

They do not execute hardware actions.

## Implemented
- Added `core/wants.py`.
- MotivationSystem now derives wants from needs, boredom, novelty, audio salience, patterns and relevant context.
- Motivation action scores receive bounded want bias.
- Motivation snapshots expose active wants and strongest want.
- MotivationCell binds body state before deriving wants.
- Added Phase 4 regression tests.

## Validation
Phase 4 + Phase 3 + Phase 2 tests: **9/9 passed**.
Python compilation passed for the changed modules.

## Acceptance target
After restart, live runtime must show active wants changing with context and those wants influencing CC action scoring while CC remains the sole decision authority.

## Boundary
Wants influence what matters; CC still decides what to do; Action/Motor still executes; consequences feed reward and learning.
