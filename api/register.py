from http.server import BaseHTTPRequestHandler
import os, json, urllib.request

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or ""

def _get(k):
    if not KV_URL or not KV_TOKEN: return {}
    try:
        req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            v = json.loads(r.read().decode()).get("result")
            return json.loads(v) if isinstance(v,str) else (v or {})
    except: return {}

def _set(k,v):
    if not KV_URL or not KV_TOKEN: return False
    try:
        sv=json.dumps(v)
        req=urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r: return True
    except: return False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(b'{"ok":true,"msg":"use POST"}')

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
                self.wfile.write(b'{"ok":false,"error":"no email/phone"}')
                return

            if 'patrol' in role or 'guard' in role:
                pending = _get("pending")
                pending[key] = {"phone":key,"email":key,"role":"patrol","status":"pending","name":name}
                _set("pending", pending)
            else:
                users = _get("users")
                users[key] = {"phone":key,"email":key,"role":"client","status":"active","name":name}
                _set("users", users)

            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            print(e)
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
