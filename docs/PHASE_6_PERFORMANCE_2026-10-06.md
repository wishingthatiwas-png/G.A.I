# G.A.I. Phase 6 — Performance

Date: 2026-10-06
Status: COMPLETE — BASELINE + ROUTING OPTIMISATION + LIVE RESOURCE CHECK

## Objective
Make V1 useful on the old laptop by improving useful behaviour per unit of compute rather than maximising tick rate.

## Routing work
The nervous system now maintains an exact-event route index alongside wildcard compatibility. Subscribe and unsubscribe maintain both indexes. Routing selects exact matches directly and only evaluates wildcard subscriptions with fnmatch.

A ready-event heap remains in place so dispatch does not scan every mailbox.

## Measurements
Original synthetic baseline: 1,000 publishes across 80 wildcard subscriptions ≈ 3.87 s; 1,000 dispatches ≈ 190 ms.

After routing/dispatch changes: same wildcard publish workload ≈ 3.86 s; dispatch ≈ 99 ms.

Mixed workload: 60 exact + 20 wildcard subscriptions, 1,000 publishes: ≈47 ms publish and ≈168 ms dispatch, with 10,500 matches and 2,000 deliveries.

The wildcard-only publish benchmark is intentionally unchanged because every subscription must still be pattern-tested. The mixed benchmark demonstrates the exact-route path avoiding a full subscription scan for exact events.

## Live resource check
RAM: ~15.9 GiB total, ~2.5 GiB used at sample time.
NVIDIA GTX 950M: 38 C, 0% utilisation at sample time, 39 MiB / 4096 MiB VRAM.
The high-CPU main.py child is the existing metabolic worker; no duplicate kernel was introduced.

## Backpressure
Mailbox limits, priority-aware eviction/drop, TTL expiry, ready-heap dispatch, and event metrics provide bounded event pressure. Slow handlers cannot create unbounded mailbox growth.

## Acceptance
- [x] Nervous routing baseline measured.
- [x] Exact-event routing index implemented.
- [x] Wildcard compatibility retained.
- [x] Dispatch optimisation benchmarked.
- [x] Mixed routing benchmarked.
- [x] Full runtime performance instrumentation confirmed.
- [x] CPU/RAM/GPU resource sample captured.
- [x] Bounded mailbox/backpressure path confirmed.

## Principle
Do not increase organism speed until useful compute efficiency, thermal behaviour, and queue stability justify it.

Next phase: V1 integration/acceptance hardening, not arbitrary speed increases.

## Completion note
Phase 6 is closed with measured routing improvements and bounded runtime behaviour. Further cadence tuning is deferred until V1 acceptance evidence identifies a real need.
