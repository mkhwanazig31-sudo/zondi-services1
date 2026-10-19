from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse, time

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_ONLY_TOKEN") or "")

try:
    from _store import get_location as _local_get, set_location as _local_set
except:
    _local_get = lambda: {}
    _local_set = lambda x: False

# In-memory fallback so patrol still sees all during test
MEM_CACHE = {}

def _get(k):
    # 1. Try KV (Vercel)
    if KV_URL and KV_TOKEN:
        try:
            req = urllib.request.Request(f"{KV_URL}/get/{k}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req, timeout=8) as r:
                v = json.loads(r.read().decode()).get("result")
                if v:
                    data = json.loads(v) if isinstance(v,str) else v
                    if data: 
                        # sync to mem
                        MEM_CACHE[k] = data
                        return data
        except: pass
    # 2. Try local file store
    try:
        d = _local_get() or {}
        if d: 
            MEM_CACHE[k]=d
            return d
    except: pass
    # 3. Mem cache (fixes Vercel cold start)
    return MEM_CACHE.get(k, {})

def _set(k,v):
    MEM_CACHE[k]=v
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
        # FIXED: Keep 2 HOURS not 15min, so you see all tested clients
        now = time.time()*1000
        cleaned={}
        for key,val in data.items():
            try:
                ts = val.get('ts') or val.get('time') or 0
                if ts>1e12: ms=ts
                elif ts>1e9: ms=ts*1000
                else: ms=now
                # FIXED: 2 hours = 7200000ms
                if (now-ms) < 7200000:
                    val['client_id']=val.get('client_id') or val.get('phone') or val.get('email') or key
                    val['name']=val.get('name') or val.get('client_id') or key.split('@')[0]
                    val['phone']=val.get('phone') or val.get('email') or key
                    val['ts']=ms
                    val['time']=ms
                    val['accuracy']=val.get('accuracy') or val.get('acc') or 0
                    cleaned[key]=val
            except: 
                cleaned[key]=val
        # DEBUG: return count
        self.wfile.write(json.dumps(cleaned).encode())
    
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            b = json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')
            key = (b.get('phone') or b.get('email') or b.get('client_id') or 'unknown').strip().lower()
            lat = float(b.get('lat') or b.get('latitude') or 0)
            lng = float(b.get('lng') or b.get('lon') or b.get('longitude') or 0)
            if abs(lat)<0.1 and abs(lng)<0.1:
                self.wfile.write(b'{"ok":false,"error":"bad coords"}'); return
            
            acc = float(b.get('accuracy') or b.get('acc') or 100)
            loc = _get("patrol_locations") or {}
            
            # FIXED: REMOVED the accuracy block that was hiding clients
            # Old code was: if acc > old_acc+20 -> return kept_old
            # Now we ALWAYS update, patrol needs live even if worse

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
            self.wfile.write(json.dumps({"ok":True, "total_clients": len(loc), "your_id": key}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
