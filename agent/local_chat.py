import json,socket,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
BODY='/mnt/gai/agent/gui/body.html'
CHAT='''<!doctype html><html><body style="background:#101216;color:#eee;font:16px sans-serif"><main style="max-width:900px;margin:auto;padding:24px"><h1>G.A.I.</h1><small>Local agent • local model • offline</small><div id="c" style="height:70vh;overflow:auto;border:1px solid #444;padding:16px"></div><input id="q" style="width:80%;padding:14px;background:#191c22;color:#fff" autofocus><button onclick="send()" style="padding:14px">Send</button><script>const c=document.getElementById('c'),q=document.getElementById('q');function add(t){let p=document.createElement('p');p.textContent=t;c.appendChild(p);c.scrollTop=c.scrollHeight}async function send(){let m=q.value.trim();if(!m)return;q.value='';add('You: '+m);let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let x=await r.json();add('G.A.I.: '+(x.message||x.error));q.focus()}q.onkeydown=e=>e.key==='Enter'&&send();add('G.A.I.: Agent online.');</script></main></body></html>'''
def ask(message):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(120);s.connect('/run/user/1000/gai-agent.sock');s.sendall(json.dumps({'message':message}).encode());data=s.recv(65536);s.close();return json.loads(data.decode())
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path=='/state':
            try:
                x=json.load(open('/mnt/gai/state/runtime.json'))
                bp='/mnt/gai/state/body_output.json'
                body=json.load(open(bp)) if os.path.exists(bp) else {}
                sched=x.get('scheduler',{})
                state={'mode':x.get('mode'),'cpu':x.get('body',{}).get('cpu',x.get('cpu',0)),'output':body.get('chars','---'),'action':body.get('action','maintain'),'tick':sched.get('tick_fps',x.get('tick','—'))}
            except Exception: state={'mode':'OFFLINE','cpu':0,'output':'---','action':'none'}
            b=json.dumps(state).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path=='/chat':
            b=CHAT.encode()
        else:
            try:b=open(BODY,'rb').read()
            except Exception:b=b'<!doctype html><body>Body unavailable</body>'
        self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'));req=json.loads(self.rfile.read(n));b=json.dumps(ask(req['message'])).encode();self.send_response(200)
        except Exception as e:b=json.dumps({'error':str(e)}).encode();self.send_response(500)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a):pass
ThreadingHTTPServer(('127.0.0.1',8090),H).serve_forever()
