from http.server import BaseHTTPRequestHandler
import json
from _store import get_users, set_users, get_pending, set_pending
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        body=json.loads(self.rfile.read(int(self.headers.get('content-length',0))).decode() or '{}')
        phone=(body.get('phone') or '').strip().lower()
        users=get_users(); pending=get_pending()
        if phone in users: del users[phone]
        if phone in pending: del pending[phone]
        set_users(users); set_pending(pending)
        self.wfile.write(json.dumps({"ok":True}).encode())
