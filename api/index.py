from http.server import BaseHTTPRequestHandler
import os, json, urllib.request
KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")
def _get(k):
    if not KV_URL or not KV_TOKEN: return {}
    try:
        req=urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            v=json.loads(r.read().decode()).get("result")
            return json.loads(v) if isinstance(v,str) else (v or {})
    except: return {}
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        try:
            users=_get("users"); pending=_get("pending")
            self.wfile.write(json.dumps({"ok":True,"users":users,"pending":pending}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
    def do_POST(self):
        self.do_GET()
