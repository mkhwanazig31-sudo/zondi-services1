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
        key=(body.get('email') or body.get('phone') or '').strip().lower()
        role=(body.get('role') or 'client').lower()
        if not key:
            self.wfile.write(json.dumps({"ok":False}).encode()); return
        if 'patrol' in role or 'guard' in role:
            pending=get_pending()
            pending[key]={"phone":key,"email":key,"role":"patrol","status":"pending","name":body.get('name',key)}
            set_pending(pending)
        else:
            users=get_users()
            users[key]={"phone":key,"email":key,"role":"client","status":"active","name":body.get('name',key)}
            set_users(users)
        self.wfile.write(json.dumps({"ok":True}).encode())
