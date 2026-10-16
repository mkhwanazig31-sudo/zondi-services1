from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse, time

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")
FILE = '/tmp/sos.json'
EXPIRE_SECONDS = 15 * 60 # 15 minutes - SOS auto-deletes after 15 min

def _clean_old(arr):
    """Remove SOS older than 15 min"""
    now = time.time()
    cleaned = []
    for item in arr:
        ts = item.get('ts') or item.get('time') or 0
        try:
            ts = float(ts)
        except:
            ts = 0
        # If no timestamp, keep it for 5 min then delete
        # If timestamp exists, check if within 15 min
        if ts == 0:
            cleaned.append(item)
        elif (now - ts) < EXPIRE_SECONDS:
            cleaned.append(item)
        else:
            print(f"Expired SOS removed: {item.get('phone')} age {(now-ts)/60:.1f}min")
    return cleaned

def _get(k):
    if KV_URL and KV_TOKEN:
        try:
            req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req, timeout=8) as r:
                v = json.loads(r.read().decode()).get("result")
                if v is not None:
                    data = json.loads(v) if isinstance(v,str) else (v or [])
                    if isinstance(data, dict): data = list(data.values())
                    if isinstance(data, list):
                        cleaned = _clean_old(data)
                        # If we cleaned, save back cleaned list
                        if len(cleaned)!= len(data):
                            _set(k, cleaned)
                        return cleaned
        except Exception as e:
            print(f"KV get fail: {e}")
    if os.path.exists(FILE):
        try:
            data = json.loads(open(FILE).read())
            if isinstance(data, dict): data = list(data.values())
            return _clean_old(data)
        except:
            return []
    return []

def _set(k,v):
    # Always clean before save
    if isinstance(v, list):
        v = _clean_old(v)
    ok = False
    if KV_URL and KV_TOKEN:
        try:
            sv = json.dumps(v)
            url = f"{KV_URL}/set/{urllib.parse.quote(k)}/{urllib.parse.quote(sv)}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"}, method="POST")
            with urllib.request.urlopen(req, timeout=8) as r:
                ok = True
        except:
            try:
                sv = json.dumps(v)
                req2 = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
                with urllib.request.urlopen(req2, timeout=8) as r:
                    ok = True
            except Exception as e:
                print(f"KV set fail: {e}")
    try:
        open(FILE,'w').write(json.dumps(v[:50] if isinstance(v,list) else v))
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

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            body = json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')

            if body.get('action') == 'clear':
                phone = (body.get('phone') or body.get('email') or '').strip().lower()
                arr = _get("sos_active")
                if isinstance(arr, dict): arr = list(arr.values())
                arr = [x for x in arr if (x.get('phone','') or x.get('email','')).lower()!= phone]
                _set("sos_active", arr)
                self.wfile.write(json.dumps({"ok": True, "cleared": True}).encode())
                return

            # New SOS - add current timestamp
            body['ts'] = time.time()
            body['time'] = body['ts']

            arr = _get("sos_active")
            if isinstance(arr, dict): arr = list(arr.values())
            if not isinstance(arr, list): arr = []

            # Remove old SOS from same phone first (prevent duplicate jumping)
            phone = (body.get('phone') or body.get('email') or '').lower()
            arr = [x for x in arr if (x.get('phone','') or x.get('email','')).lower()!= phone]

            arr.insert(0, body)
            arr = arr[:20]

            _set("sos_active", arr)
            self.wfile.write(json.dumps({"ok": True, "expires_in": "15min"}).encode())
        except Exception as e:
            print(e)
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            arr = _get("sos_active")
            self.wfile.write(json.dumps(arr or []).encode())
        except Exception as e:
            print(e)
            self.wfile.write(b'[]')
