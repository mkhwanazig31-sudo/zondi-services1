from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse, time

KV_URL = (os.environ.get("KV_REST_API_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or "")

def kv_get(k):
    if KV_URL and KV_TOKEN:
        try:
            req=urllib.request.Request(f"{KV_URL}/get/{k}",headers={"Authorization":f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req,timeout=5) as r:
                v=json.loads(r.read().decode()).get("result")
                return json.loads(v) if v and isinstance(v,str) else (v or [])
        except: pass
    return []

def kv_set(k,v):
    if KV_URL and KV_TOKEN:
        try:
            sv=json.dumps(v)
            url=f"{KV_URL}/set/{urllib.parse.quote(k)}/{urllib.parse.quote(sv)}"
            req=urllib.request.Request(url,headers={"Authorization":f"Bearer {KV_TOKEN}"},method="POST")
            with urllib.request.urlopen(req,timeout=5): pass
        except: pass

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
        alerts=kv_get("zondi_sos")
        if not isinstance(alerts,list): alerts=[alerts] if alerts else []
        now=time.time()
        # AUTO-OFF 15 min + keep best accuracy per client
        filtered=[]
        best_by_phone={}
        for a in alerts:
            try:
                ts=a.get('ts') or a.get('time') or 0
                if ts>1e12: ts=ts/1000
                if (now-ts) > 900: continue # 15 min expire
                phone=(a.get('phone') or '').lower()
                acc=float(a.get('accuracy') or a.get('acc') or 999)
                if phone not in best_by_phone or acc < float(best_by_phone[phone].get('accuracy') or 999):
                    best_by_phone[phone]=a
            except: continue
        filtered=list(best_by_phone.values())
        filtered.sort(key=lambda x: x.get('ts',0), reverse=True)
        self.wfile.write(json.dumps(filtered).encode())
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            length=int(self.headers.get('content-length',0) or 0)
            body=json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')
            if body.get('action')=='clear':
                phone=(body.get('phone') or '').lower()
                alerts=kv_get("zondi_sos")
                if phone:
                    alerts=[a for a in alerts if (a.get('phone','').lower()!=phone)]
                else:
                    alerts=[]
                kv_set("zondi_sos",alerts)
                self.wfile.write(b'{"ok":true,"cleared":true}')
                return
            alerts=kv_get("zondi_sos")
            if not isinstance(alerts,list): alerts=[]
            # Block bad accuracy SOS >20m
            acc=float(body.get('accuracy') or body.get('acc') or 0)
            if acc>20:
                self.wfile.write(json.dumps({"ok":False,"error":f"Bad accuracy {acc}m, need <20m"}).encode())
                return
            body['ts']=body.get('ts') or int(time.time()*1000)
            body['time']=body['ts']
            alerts.append(body)
            # Keep only last 20
            alerts=alerts[-20:]
            kv_set("zondi_sos",alerts)
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
