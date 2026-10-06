"""Privacy-first OpenAI bridge for G.A.I.
Only explicitly supplied G.A.I. context is sent; no personal ChatGPT context is imported.
"""
import json, os
from pathlib import Path
from openai import OpenAI

ROOT=Path('/mnt/gai')
HISTORY=ROOT/'state/openai_gai_chat.json'
MODEL=os.getenv('GAI_OPENAI_MODEL','gpt-6-luna')
SYSTEM='''You are the external cognitive interface for G.A.I., a local embodied autonomous-agent experiment.\nTreat G.A.I. as the subject. Do not ask for or infer the human operator's personal information. Use only the G.A.I. state/context explicitly provided in the request. Be concise and technically grounded.'''

def load_history():
    if not HISTORY.exists(): return []
    try: return json.loads(HISTORY.read_text())
    except Exception: return []

def save_history(h):
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    HISTORY.write_text(json.dumps(h[-40:],indent=2))

def chat(message, context=None):
    if not isinstance(message,str) or not message.strip(): raise ValueError('message required')
    # Deliberate allowlist: context is a plain G.A.I. payload, never arbitrary files/env/profile data.
    safe_context=context if isinstance(context,dict) else {}
    history=load_history()
    user=json.dumps({'message':message,'gai_context':safe_context},ensure_ascii=False)
    client=OpenAI()
    response=client.responses.create(model=MODEL,input=[{'role':'system','content':SYSTEM},*history,{'role':'user','content':user}])
    answer=response.output_text
    history += [{'role':'user','content':user},{'role':'assistant','content':answer}]
    save_history(history)
    return answer

if __name__=='__main__':
    import sys
    print(chat(' '.join(sys.argv[1:]) or 'Report your current interface status.'))
