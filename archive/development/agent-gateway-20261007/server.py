from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from .gai_openai_bridge import chat

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/chat': self.send_error(404); return
        try:
            n=int(self.headers.get('Content-Length','0')); body=json.loads(self.rfile.read(n))
            answer=chat(body.get('message',''), body.get('gai_context',{}))
            data=json.dumps({'answer':answer}).encode()
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        except Exception as e:
            data=json.dumps({'error':str(e)}).encode(); self.send_response(500); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*args): pass

HTTPServer(('127.0.0.1',8765),Handler).serve_forever()
