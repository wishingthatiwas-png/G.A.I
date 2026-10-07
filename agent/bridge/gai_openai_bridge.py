"""Privacy-first OpenAI bridge for G.A.I.
Only explicitly supplied G.A.I. context is sent; no personal ChatGPT context is imported.
"""

import hashlib
import json
import os
from pathlib import Path

from openai import OpenAI

ROOT = Path("/mnt/gai")
HISTORY = ROOT / "state/openai_gai_chat.json"
HISTORY_DIR = ROOT / "state/openai_gai_sessions"
MODEL = os.getenv("GAI_OPENAI_MODEL", "gpt-6-luna")
SYSTEM = """You are the external cognitive interface for G.A.I., a local embodied autonomous-agent experiment.
Treat G.A.I. as the subject. Do not ask for or infer the human operator's personal information.
Use only the G.A.I. state/context explicitly provided in the request. Be concise and technically grounded."""


def _history_path(history_key: str | None) -> Path:
    if not history_key:
        return HISTORY
    digest = hashlib.sha256(history_key.encode("utf-8")).hexdigest()[:24]
    return HISTORY_DIR / f"{digest}.json"


def load_history(history_key: str | None = None):
    path = _history_path(history_key)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(h, history_key: str | None = None):
    path = _history_path(history_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(h[-40:], indent=2, ensure_ascii=False))


def chat(message, context=None, history_key: str | None = None):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message required")

    # Deliberate allowlist: context is a plain G.A.I. payload, never arbitrary files/env/profile data.
    safe_context = context if isinstance(context, dict) else {}
    history = load_history(history_key)
    user = json.dumps(
        {"message": message, "gai_context": safe_context},
        ensure_ascii=False,
    )

    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM},
            *history,
            {"role": "user", "content": user},
        ],
    )
    answer = response.output_text
    history += [
        {"role": "user", "content": user},
        {"role": "assistant", "content": answer},
    ]
    save_history(history, history_key)
    return answer


if __name__ == "__main__":
    import sys

    print(chat(" ".join(sys.argv[1:]) or "Report your current interface status."))
