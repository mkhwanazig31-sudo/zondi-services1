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
            if v is None: return {}
            if isinstance(v, str):
                try: return json.loads(v)
                except: return {}
            return v if isinstance(v, dict) else {}
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
        self.send_header('Access-Control-Allow-Methods','POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            raw = self.rfile.read(length).decode() if length else '{}'
            body = json.loads(raw) if raw else {}
            raw_key = (body.get('email') or body.get('phone') or '').strip()
            if not raw_key:
                self.wfile.write(b'{"ok":false,"error":"no key"}')
                return
            
            keys_to_try = [raw_key, raw_key.lower()]
            
            # All possible storage keys
            pending_hashes = ["pending", "zondi_pending", "zondi_pending_cache"]
            user_hashes = ["users", "zondi_users"]
            
            found_user = None
            
            # Find in any pending hash (case-insensitive)
            for ph in pending_hashes:
                pending = _get(ph)
                if not pending: continue
                for search_key in keys_to_try:
                    # exact
                    if search_key in pending:
                        found_user = pending[search_key]
                        del pending[search_key]
                        _set(ph, pending)
                        break
                    # case-insensitive
                    for existing in list(pending.keys()):
                        if existing.lower() == search_key.lower():
                            found_user = pending[existing]
                            del pending[existing]
                            _set(ph, pending)
                            break
                    if found_user: break
                if found_user: break

            if found_user:
                found_user['status'] = 'active'
                if isinstance(found_user, str):
                    found_user = {"role":"patrol","status":"active","name":found_user}
                # Save to ALL user hashes
                for uh in user_hashes:
                    users = _get(uh)
                    if not isinstance(users, dict): users = {}
                    # save with original key case
                    users[raw_key] = found_user
                    # also save lower for safety
                    users[raw_key.lower()] = found_user
                    _set(uh, users)

            self.wfile.write(json.dumps({"ok":True, "approved":raw_key}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self): self.do_POST()
