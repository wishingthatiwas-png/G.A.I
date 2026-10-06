# G.A.I.-CC-V1 — Central Cognitive Core

## Purpose

CC-V1 is G.A.I.'s first central cognitive circuit. The language model is a reasoning substrate inside the circuit, not the organism itself.

## Circuit

Senses/perception → processed events → nervous system → **Global Workspace** → memory recall → reasoning model → structured thought/intention/prediction → safe action shell → consequences → nervous system → workspace.

## Global Workspace

The workspace is finite and inspectable: current experience, body state, concerns/drives, recalled memories, predictions, recent consequences, self model, current thought summary, current intention, and uncertainty/confidence.

Raw sensor streams do not go directly to the reasoning model.

## Model boundary

The model receives a compact CC-V1 prompt and must return structured data. CC-V1 validates the intention against a fixed allow-list. The model never executes hardware actions directly.

The action shell currently accepts only safe operations such as observation, maintenance, rest and sandboxed creative artifacts.

## Memory boundary

CC-V1 reads the existing tiered Memory subsystem. Memory remains responsible for persistence and consolidation; CC-V1 decides what is currently relevant to thought.

## Runtime

config/agent.json enables central_cognition_v1.

The kernel schedules CC-V1 outside the main tick loop: awake approximately every 8 seconds; dream approximately every 45 seconds.

The legacy LocalAgent remains as a compatibility and action shell. Its autonomous language loop is disabled while CC-V1 is enabled.

## Verification

Current focused suite: 18 passed across CC-V1, nervous-system and kernel tests.

A live model probe successfully constructed the CC-V1 component and reached the local Qwen server, but the model response exceeded the short remote test window. This is a latency/budget issue to solve next, not a structural CC failure.

## Non-claim

CC-V1 does not establish consciousness. It establishes a persistent, embodied, inspectable central cognitive architecture in which consciousness-like phenomena can be investigated experimentally.
