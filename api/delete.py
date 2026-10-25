from http.server import BaseHTTPRequestHandler
import os, json, urllib.request
KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or ""

def _get(k):
    if not KV_URL or not KV_TOKEN: return {}
    try:
        req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            v = data.get("result")
            if v is None: return {}
            if isinstance(v, str):
                try: return json.loads(v)
                except: return {}
            return v if isinstance(v, dict) else {}
    except Exception as e:
        print(f"_get {k} error: {e}")
        return {}

def _set(k,v):
    if not KV_URL or not KV_TOKEN: return False
    try:
        sv=json.dumps(v)
        # FIX: Use correct REST format
        req=urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r: 
            return True
    except Exception as e:
        print(f"_set {k} error: {e}")
        return False

def _hdel(hash_key, field):
    if not KV_URL or not KV_TOKEN: return
    try:
        req = urllib.request.Request(f"{KV_URL}/hdel/{hash_key}/{field}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r: pass
    except: pass

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, GET, DELETE, OPTIONS')
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
            # FIX: Keep original + lower + trimmed versions
            raw_key = (body.get('email') or body.get('phone') or '').strip()
            if not raw_key:
                self.wfile.write(b'{"ok":false,"error":"no key"}')
                return
            
            keys_to_try = [raw_key, raw_key.lower(), raw_key.strip().lower()]
            keys_to_try = list(dict.fromkeys(keys_to_try)) # unique

            # FIX: Delete from ALL possible storage keys!
            all_hashes = ["users", "pending", "zondi_users", "zondi_pending", "zondi_pending_cache", "zondi_patrol_cache"]
            
            for hash_name in all_hashes:
                data = _get(hash_name)
                if not data or not isinstance(data, dict): continue
                changed = False
                for k in keys_to_try:
                    if k in data:
                        del data[k]
                        changed = True
                    # Also try case-insensitive search
                    for existing in list(data.keys()):
                        if existing.lower() == k.lower():
                            del data[existing]
                            changed = True
                if changed:
                    _set(hash_name, data)
                    print(f"Deleted {keys_to_try} from {hash_name}")

            # Also try HDEL for hash structures
            for k in keys_to_try:
                for h in all_hashes:
                    _hdel(h, k)

            self.wfile.write(json.dumps({"ok":True, "deleted":raw_key, "tried":keys_to_try}).encode())
        except Exception as e:
            print(f"delete error: {e}")
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self): self.do_POST()
    def do_DELETE(self): self.do_POST()
