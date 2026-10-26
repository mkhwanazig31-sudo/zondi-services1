from http.server import BaseHTTPRequestHandler
import os, json, urllib.request

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or os.environ.get("KV_REST_API_TOKEN") or "")

def _get(k):
    if not KV_URL or not KV_TOKEN: return {}
    try:
        req=urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode()
            data = json.loads(raw)
            v = data.get("result")
            if v is None: return {}
            if isinstance(v, str):
                try: return json.loads(v)
                except: return {}
            return v if isinstance(v, dict) else {}
    except Exception as e:
        print(f"_get {k} error: {e}")
        return {}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma','no-cache')
        self.end_headers()
        try:
            # MERGE ALL POSSIBLE KEYS - THIS FIXES YOUR 2 DOMAINS BUG!
            all_user_hashes = ["users", "zondi_users", "zondi_users_v2"]
            all_pending_hashes = ["pending", "zondi_pending", "zondi_pending_cache"]
            
            merged_users = {}
            merged_pending = {}
            
            for h in all_user_hashes:
                d = _get(h)
                if isinstance(d, dict):
                    merged_users.update(d)
            
            for h in all_pending_hashes:
                d = _get(h)
                if isinstance(d, dict):
                    merged_pending.update(d)

            # Also remove any deleted keys that might linger in other hashes
            # If key is not in primary 'users', don't include from secondary
            
            self.wfile.write(json.dumps({
                "ok":True,
                "users":merged_users,
                "pending":merged_pending,
                # also return counts for debug
                "debug_counts": {
                    "users": len(merged_users),
                    "pending": len(merged_pending)
                }
            }).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_POST(self):
        self.do_GET()
