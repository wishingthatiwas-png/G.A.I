# G.A.I. Agent Gateway

A local arbitration layer for multiple external agent sessions.

## Contract

External agents are collaborators, not competing cognition loops.

Each request carries:
- agent_id
- session_id
- correlation_id
- bounded capability permissions
- explicit G.A.I. context

Chat sessions have separate local histories.

Command requests are **queued and serialized** through the existing G.A.I.
user-command boundary. The gateway never calls a motor organ directly.
G.A.I.'s UserCommandCell evaluates the request and may agree or decline.

## Endpoints

GET /health
GET /agents

POST /v1/chat
POST /v1/command

Default bind: 127.0.0.1:8766

## Security

The gateway is loopback-only by default. Unknown agent IDs are denied.
Only configured agents may chat/request commands.
Only the existing V1 command set is accepted: move, sleep, wake.

This is an integration layer; central cognition remains authoritative.
