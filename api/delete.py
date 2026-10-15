from http.server import BaseHTTPRequestHandler
import json
from _store import get_users, set_users, get_pending, set_pending
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            b=json.loads(self.rfile.read(int(self.headers.get('content-length',0) or 0)).decode() or '{}')
            key=(b.get('phone') or b.get('email') or '').strip().lower()
            u=get_users() or {}
            p=get_pending() or {}
            if key in u: del u[key]
            if key in p: del p[key]
            set_users(u)
            set_pending(p)
            self.wfile.write(json.dumps({"ok":True}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
        
