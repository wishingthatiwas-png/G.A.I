# Digital Memory Docking Protocol

1. Detect attachment.
2. Identify expected G.A.I. archive label/UUID.
3. Mount read-only for inspection.
4. Verify filesystem and archive manifest.
5. Load index and memory metadata.
6. Expose deep memory to the memory subsystem.
7. During deep sleep, enable staged writes.
8. Flush + verify before marking memories committed.
9. On removal, close handles and unmount cleanly.

The first implementation should use explicit user/system mount handling rather than automatic arbitrary-device execution.
