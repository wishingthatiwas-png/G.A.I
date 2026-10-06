# G.A.I. Deep Archive

The deep archive is designed as a detachable memory organ. The HDD may be connected or disconnected without making it a dependency of the running brain.

## Memory lifecycle
- AWAKE: active/working memory remains on SSD. No deep-memory writes.
- PRE_SLEEP: rank and prepare candidates for consolidation.
- DEEP SLEEP / DREAM: compress selected experiences into symbolic scene/text representations, associate emotion/context, and commit them to the deep archive.
- WAKE: deep archive is read-only/inactive until the next sleep cycle.

## Docking model
The HDD is treated as a removable digital memory module. When attached, G.A.I. detects it, verifies its identity/filesystem, mounts it at a stable path, validates the archive manifest, and makes it available to memory services. When detached, G.A.I. falls back to SSD memory and marks deep memory unavailable. No live cognition should depend on the HDD being present.

## Safety
Writes should use staging + verification before committing. Unknown/unverified disks belong in quarantine. Never blindly mount or execute content from a newly attached disk.
