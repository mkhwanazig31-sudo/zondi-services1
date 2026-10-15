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
        body=json.loads(self.rfile.read(int(self.headers.get('content-length',0))).decode() or '{}')
        phone=(body.get('phone') or '').strip().lower()
        pending=get_pending()
        users=get_users()
        if phone in pending:
            users[phone]={**pending[phone],"status":"active"}
            del pending[phone]
            set_users(users); set_pending(pending)
            self.wfile.write(json.dumps({"ok":True,"from":"pending"}).encode()); return
        if phone in users:
            users[phone]["status"]="active"; set_users(users)
            self.wfile.write(json.dumps({"ok":True}).encode()); return
        self.wfile.write(json.dumps({"ok":False,"error":"not found"}).encode())
