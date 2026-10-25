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
    except Exception as e:
        print(f"_set error {e}")
        return False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        try:
            length=int(self.headers.get('content-length',0) or 0)
            raw=self.rfile.read(length).decode() if length else '{}'
            body=json.loads(raw) if raw else {}
            
            old_phone=(body.get('old_phone') or body.get('phone') or body.get('email') or '').strip()
            new_phone=(body.get('new_phone') or old_phone).strip()
            if not old_phone:
                self.wfile.write(json.dumps({"ok":False,"error":"no key"}).encode())
                return

            # Update in ALL hashes
            for hash_name in ["users", "zondi_users", "pending", "zondi_pending"]:
                data = _get(hash_name)
                if not data or not isinstance(data, dict): continue
                
                # Find key case-insensitive
                actual_key = None
                for k in data.keys():
                    if k.lower() == old_phone.lower() or k == old_phone:
                        actual_key = k
                        break
                
                if actual_key and actual_key in data:
                    u = data[actual_key]
                    if isinstance(u, str): u = {"name":u, "role":"client", "status":"active"}
                    
                    if body.get('name'): u['name']=body['name']
                    if body.get('client_id'): u['client_id']=body['client_id']
                    if body.get('role'): u['role']=body['role']
                    if body.get('camBrand') is not None: u['camBrand']=body['camBrand']
                    if body.get('camId') is not None: u['camId']=body['camId']
                    if body.get('camUrl') is not None: 
                        u['camUrl']=body['camUrl']
                        u['rtsp']=body['camUrl']
                        u['hls']=body['camUrl']
                    
                    if new_phone != actual_key:
                        # Rename
                        data[new_phone] = u
                        del data[actual_key]
                        # also clean lower duplicate
                        if old_phone.lower() in data and old_phone.lower() != new_phone:
                            del data[old_phone.lower()]
                    else:
                        data[actual_key]=u
                    
                    _set(hash_name, data)

            self.wfile.write(json.dumps({"ok":True}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self): self.do_POST()
