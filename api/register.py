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
            length = int(self.headers.get('content-length',0) or 0)
            raw = self.rfile.read(length).decode() if length else '{}'
            body = json.loads(raw or '{}')
            key = (body.get('email') or body.get('phone') or '').strip().lower()
            role = (body.get('role') or 'client').lower()
            name = body.get('name') or key

            if not key:
                self.wfile.write(json.dumps({"ok":False,"error":"no email"}).encode())
                return

            if 'patrol' in role or 'guard' in role:
                pending = get_pending() or {}
                pending[key] = {"phone":key,"email":key,"role":"patrol","status":"pending","name":name}
                set_pending(pending)
                print(f"Added pending: {key}")
            else:
                users = get_users() or {}
                users[key] = {"phone":key,"email":key,"role":"client","status":"active","name":name}
                set_users(users)
                print(f"Added client: {key}")

            self.wfile.write(json.dumps({"ok":True}).encode())
        except Exception as e:
            print("register error", e)
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps({"ok":True,"msg":"use POST"}).encode())
