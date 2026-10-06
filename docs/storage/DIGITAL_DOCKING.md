# G.A.I. Digital Docking System

The long-term-memory HDD is intended to be detachable. The architecture must not depend on its permanent presence.

## Principle
SSD = active body/brain.
HDD = detachable deep-memory organ.

The system should detect the deep-memory volume by filesystem label/UUID rather than assuming a device path. A missing archive must degrade safely to `deep_memory_offline`; G.A.I. continues operating with SSD memory.

## Dock lifecycle
1. Detect archive volume.
2. Verify filesystem identity and expected structure.
3. Mount at a stable path such as `/mnt/gai-deep`.
4. Run integrity/index checks.
5. Mark deep memory ONLINE.
6. On removal, stop writes, flush queues, unmount safely and mark OFFLINE.

## Safety
No long-term-memory writes while the volume is being detached. Deep-sleep consolidation must refuse to start if the archive is unavailable or integrity checks fail.

## Next implementation
The physical archive organ is now detected and identity-verified on the current laptop, but it is intentionally not mounted or writable. The remaining work is the actual docking service, archive manifest/index, mount detection and clean detach workflow. Do not couple the organism to `/dev/sdb`; identity must come from filesystem label/UUID and verified structure.
