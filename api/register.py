from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.parse

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or ""

def _get(k):
    if not KV_URL or not KV_TOKEN:
        print("KV MISSING - get failed")
        return {}
    try:
        req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            v = data.get("result")
            if v is None: return {}
            return json.loads(v) if isinstance(v,str) else (v or {})
    except Exception as e:
        print(f"_get error {k}: {e}")
        return {}

def _set(k,v):
    if not KV_URL or not KV_TOKEN:
        print("KV MISSING - set failed, check Vercel env vars!")
        return False
    try:
        sv=json.dumps(v)
        # Try method 1: POST to /set/key with value
        enc_val = urllib.parse.quote(sv)
        url = f"{KV_URL}/set/{urllib.parse.quote(k)}/{enc_val}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                print(f"_set success {k} via /set")
                return True
        except Exception as e1:
            print(f"_set method1 fail {e1}, trying pipeline")
            # Method 2: pipeline POST to base URL
            req2 = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
            with urllib.request.urlopen(req2, timeout=5) as r:
                print(f"_set success {k} via pipeline")
                return True
    except Exception as e:
        print(f"_set final fail {k}: {e}")
        return False

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
            password = body.get('password') or ''
            status = body.get('status') or ('pending' if 'patrol' in role else 'active')
            if not key:
                self.wfile.write(b'{"ok":false,"error":"no email/phone"}')
                return
            ok=False
            if 'patrol' in role or 'guard' in role:
                pending = _get("pending")
                pending[key] = {"phone":key,"email":key,"role":"patrol","status":status,"name":name,"password":password, "created": __import__("time").time()}
                ok = _set("pending", pending)
            else:
                users = _get("users")
                users[key] = {"phone":key,"email":key,"role":"client","status":status,"name":name,"password":password, "created": __import__("time").time()}
                ok = _set("users", users)

            if not ok:
                # Tell frontend KV failed!
                self.wfile.write(json.dumps({"ok":False,"error":"KV not configured - add KV_REST_API_URL & TOKEN in Vercel! Data only in localStorage"}).encode())
            else:
                self.wfile.write(json.dumps({"ok":True, "saved":True}).encode())
        except Exception as e:
            print(e)
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
