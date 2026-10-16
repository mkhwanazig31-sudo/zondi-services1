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
        self.send_response(200); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','POST, OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers()
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            body = json.loads(self.rfile.read(length).decode() or '{}')
            key = (body.get('email') or body.get('phone') or '').strip().lower()
            users = _get("users"); pending = _get("pending")
            if key in users: del users[key]
            if key in pending: del pending[key]
            _set("users", users); _set("pending", pending)
            self.wfile.write(b'{"ok":true}')
        except Exception as e: self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
    def do_GET(self): self.do_POST()
