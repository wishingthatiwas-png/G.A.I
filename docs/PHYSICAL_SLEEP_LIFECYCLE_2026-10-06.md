# G.A.I. Physical Sleep Lifecycle — 2026-10-06

## Purpose
Closing the physical laptop lid is a non-vetoable body event. It forces G.A.I. through the existing lifecycle rather than asking Central Consciousness whether it wants to sleep.

## Flow
Lid closed
→ Lid/Sleep Bridge blocks the desktop lid action
→ physical lifecycle request
→ pre_sleep
→ maintenance + neural preparation
→ dream/consolidation
→ physical sleep latch
→ laptop suspend

Lid opened
→ bridge resumes
→ physical wake request
→ wake
→ sensory organs reopen
→ awake

## Separation
- Lid detection is an external body/system signal.
- Central Consciousness cannot veto physical sleep.
- Lifecycle owns phase transitions.
- Neural Fabric receives explicit physical-sleep session boundaries.
- Organs are released/reopened through lifecycle.
- Toys are environment objects and are not part of the sleep mechanism.

## Neural integration points
Current safe hooks:
- physiology.lid_closed
- physiology.lid_opened
- NeuralFabric.begin_physical_sleep()
- NeuralFabric.end_physical_sleep()
- pre_sleep plasticity
- dream replay/consolidation
- wake plasticity

Future neural work can add:
- sleep-dependent structural reorganisation
- dormant/stable connection promotion
- dream replay schedules
- resource-aware neural pruning
- sleep-session duration as an experience variable

These hooks do not currently add autonomous neural behaviour beyond the existing V1 neural fabric.

## Safety / reliability
A systemd-inhibit handle-lid-switch blocker is held by the sleep bridge. If the bridge dies, its inhibitor disappears and normal desktop lid behaviour returns.

The camera stream was hardened because physical sleep closes the camera while its capture thread may be reading. Capture and release now share a lock to prevent native OpenCV races.

## Validation
Dry-run validated:
physical sleep request → dream + neural sleep session → physical wake request → awake.

A real lid-close test is intentionally left as the final hardware validation because it suspends the development machine.
