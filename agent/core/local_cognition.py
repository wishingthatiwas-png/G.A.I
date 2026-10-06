from __future__ import annotations
import json, urllib.request
from pathlib import Path

ROOT=Path("/mnt/gai")
IDENTITY=ROOT/"config/identity.json"
DEFAULT_URL="http://127.0.0.1:8080/v1/chat/completions"

class LocalCognition:
    def __init__(self, url=DEFAULT_URL):
        self.url=url
        self.identity=json.loads(IDENTITY.read_text()) if IDENTITY.exists() else {}

    def system_prompt(self, context=None):
        base=("You are the local cognitive model of G.A.I., an artificial-life research agent. "
              "You are not the human creator and must not assume access to the creator's personal data. "
              "Use only the identity and explicit G.A.I. context supplied. "
              "Reason from current body state, perception, memory and goals. "
              "Be concise unless deeper reasoning is needed.")
        return base+"\nG.A.I. identity:\n"+json.dumps(self.identity,indent=2)+"\nContext:\n"+json.dumps(context or {},indent=2)

    def chat(self, message, context=None, timeout=60):
        payload={"model":"Qwen3-4B","messages":[
            {"role":"system","content":self.system_prompt(context)},
            {"role":"user","content":message}
        ],"temperature":0.7,"stream":False}
        req=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            data=json.loads(r.read())
        return data["choices"][0]["message"]["content"]
