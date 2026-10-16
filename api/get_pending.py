from http.server import BaseHTTPRequestHandler
import os, json, urllib.request
KV_URL = (os.environ.get("KV_REST_API_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")
def _get(k):
    try:
        req=urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            v=json.loads(r.read().decode()).get("result")
            return json.loads(v) if isinstance(v,str) else (v or {})
    except: return {}
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        self.wfile.write(json.dumps({"ok":True,"pending":_get("pending")}).encode())
