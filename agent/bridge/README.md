# G.A.I. OpenAI Bridge

A separate, privacy-first API interface between G.A.I. and an OpenAI model.

## Privacy boundary
- Does not use the Firefox/ChatGPT session.
- Does not import ChatGPT memory.
- Does not read the operator's personal profile.
- Sends only the explicit message + `gai_context` supplied by G.A.I.
- Conversation history is kept locally at `/mnt/gai/state/openai_gai_chat.json`.
- API key is supplied through `OPENAI_API_KEY`; never hard-code it.

Uses the OpenAI Responses API.
