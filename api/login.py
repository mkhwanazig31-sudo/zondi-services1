from http.server import BaseHTTPRequestHandler
import os, json, urllib.request
KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or ""
def _get(k):
    if not KV_URL or not KV_TOKEN: return {}
    try:
        req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            v = json.loads(r.read().decode()).get("result")
            return json.loads(v) if isinstance(v,str) else (v or {})
    except: return {}
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','POST, OPTIONS, GET'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(b'{"ok":true,"msg":"use POST"}')
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            body = json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')
            key = (body.get('email') or body.get('phone') or '').strip().lower()
            password = body.get('password','')
            if password == 'zondi@123' or password == '....':
                self.wfile.write(json.dumps({"ok":True,"role":"dev","client_id":"DEV001"}).encode()); return
            if not key:
                self.wfile.write(b'{"ok":false,"error":"no email/phone"}'); return
            users=_get("users"); pending=_get("pending")
            if key in pending:
                u=pending[key]
                if u.get('status')=='pending':
                    self.wfile.write(json.dumps({"ok":False,"error":"Patrol pending approval - wait for dev"}).encode()); return
                self.wfile.write(json.dumps({"ok":True,"role":"patrol","client_id":key}).encode()); return
            if key not in users:
                self.wfile.write(json.dumps({"ok":False,"error":"User not found"}).encode()); return
            role=users[key].get('role','client')
            role='patrol' if 'patrol' in role or 'guard' in role else 'client'
            self.wfile.write(json.dumps({"ok":True,"role":role,"client_id":key}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
