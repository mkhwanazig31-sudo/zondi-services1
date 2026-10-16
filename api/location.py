from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse, time

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")

try:
    from _store import get_location as _local_get, set_location as _local_set
except:
    _local_get = lambda: {}
    _local_set = lambda x: False

def _get(k):
    if KV_URL and KV_TOKEN:
        try:
            req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req, timeout=8) as r:
                v = json.loads(r.read().decode()).get("result")
                if v:
                    data = json.loads(v) if isinstance(v,str) else v
                    if data: return data
        except: pass
    try:
        return _local_get() or {}
    except:
        return {}

def _set(k,v):
    if KV_URL and KV_TOKEN:
        try:
            sv = json.dumps(v)
            url = f"{KV_URL}/set/{urllib.parse.quote(k)}/{urllib.parse.quote(sv)}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"}, method="POST")
            with urllib.request.urlopen(req, timeout=8): pass
        except:
            try:
                sv = json.dumps(v)
                req2 = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET",k,sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}","Content-Type":"application/json"}, method="POST")
                with urllib.request.urlopen(req2, timeout=8): pass
            except: pass
    try: _local_set(v)
    except: pass

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        data = _get("patrol_locations") or {}
        # CLEAN: Remove old >15min and ensure fields exist
        now = time.time()*1000
        cleaned={}
        for key,val in data.items():
            try:
                ts = val.get('ts') or val.get('time') or 0
                if ts>1e12: ms=ts
                elif ts>1e9: ms=ts*1000
                else: ms=now
                # Keep only last 15 min
                if (now-ms) < 900000:
                    # Ensure required fields
                    val['client_id']=val.get('client_id') or val.get('phone') or val.get('email') or key
                    val['name']=val.get('name') or val.get('client_id') or key.split('@')[0]
                    val['phone']=val.get('phone') or val.get('email') or key
                    val['ts']=ms
                    val['accuracy']=val.get('accuracy') or val.get('acc') or 0
                    cleaned[key]=val
            except: cleaned[key]=val
        self.wfile.write(json.dumps(cleaned).encode())
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            b = json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')
            key = (b.get('phone') or b.get('email') or b.get('client_id') or 'unknown').strip().lower()
            lat = float(b.get('lat') or b.get('latitude') or 0)
            lng = float(b.get('lng') or b.get('lon') or b.get('longitude') or 0)
            # Ignore bad coords (0,0)
            if abs(lat)<0.1 and abs(lng)<0.1:
                self.wfile.write(b'{"ok":false,"error":"bad coords"}'); return
            # Only accept high accuracy <50m, else ignore old low accuracy
            acc = float(b.get('accuracy') or b.get('acc') or 100)
            loc = _get("patrol_locations") or {}
            old = loc.get(key)
            if old and old.get('accuracy') and acc>old.get('accuracy')+20:
                # New reading worse than old, keep old
                self.wfile.write(json.dumps({"ok":True,"kept_old":True}).encode()); return

            now_ms = int(time.time()*1000)
            loc[key] = {
                "client_id": b.get('client_id') or b.get('phone') or b.get('email') or key,
                "name": b.get('name') or (b.get('email') or key).split('@')[0],
                "phone": b.get('phone') or b.get('email') or key,
                "email": b.get('email') or b.get('phone') or key,
                "lat": lat, "lng": lng,
                "accuracy": acc,
                "acc": acc,
                "ts": now_ms,
                "time": now_ms,
                "sos": bool(b.get('sos'))
            }
            _set("patrol_locations", loc)
            self.wfile.write(json.dumps({"ok":True}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
