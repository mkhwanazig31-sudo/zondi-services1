from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")

# Try import _store for local fallback, but main is KV
try:
    from _store import get_location as _local_get, set_location as _local_set
except:
    _local_get = lambda: {}
    _local_set = lambda x: False

def _get(k):
    # 1. Try KV first (persists forever)
    if KV_URL and KV_TOKEN:
        try:
            req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req, timeout=8) as r:
                v = json.loads(r.read().decode()).get("result")
                if v is None:
                    pass
                else:
                    data = json.loads(v) if isinstance(v,str) else (v or {})
                    if data: return data
        except Exception as e:
            print(f"KV get fail: {e}")
    # 2. Fallback to local _store
    try:
        return _local_get() or {}
    except:
        return {}

def _set(k,v):
    ok = False
    # 1. Try KV
    if KV_URL and KV_TOKEN:
        try:
            sv = json.dumps(v)
            url = f"{KV_URL}/set/{urllib.parse.quote(k)}/{urllib.parse.quote(sv)}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"}, method="POST")
            with urllib.request.urlopen(req, timeout=8) as r:
                ok = True
                print(f"KV set success {k}")
        except Exception as e1:
            print(f"KV set method1 fail {e1}, trying pipeline")
            try:
                sv = json.dumps(v)
                req2 = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
                with urllib.request.urlopen(req2, timeout=8) as r:
                    ok = True
            except Exception as e2:
                print(f"KV set fail {e2}")
    # 2. Also save to local _store as backup
    try:
        _local_set(v)
    except:
        pass
    return ok

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
        self.end_headers()
        try:
            data = _get("patrol_locations")
            print(f"GET locations: {len(data)} patrols")
            self.wfile.write(json.dumps(data or {}).encode())
        except Exception as e:
            print(e)
            self.wfile.write(b'{}')
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            raw = self.rfile.read(length).decode() if length else '{}'
            b = json.loads(raw or '{}')
            key = (b.get('phone') or b.get('email') or 'unknown').strip().lower()
            lat = b.get('lat') or b.get('latitude') or 0
            lng = b.get('lng') or b.get('lon') or b.get('longitude') or 0
            loc = _get("patrol_locations") or {}
            loc[key] = {"lat": float(lat), "lng": float(lng), "time": b.get('time',''), "phone": key, "email": key}
            _set("patrol_locations", loc)
            self.wfile.write(json.dumps({"ok": True, "saved": len(loc)}).encode())
        except Exception as e:
            print(e)
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
