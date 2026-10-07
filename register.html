from http.server import BaseHTTPRequestHandler
import json, os
FILE='/tmp/zondi_users.json'
def load():
    if not os.path.exists(FILE): return {}
    try:
        with open(FILE,'r') as f: return json.load(f)
    except: return {}
def save(d):
    with open(FILE,'w') as f: json.dump(d,f)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        length=int(self.headers.get('content-length',0))
        try:
            body=json.loads(self.rfile.read(length).decode())
            phone=body.get('phone','').strip()
            password=body.get('password','')
            role=body.get('role','client')
            if not phone or not password:
                self.wfile.write(json.dumps({"ok":False,"msg":"Missing fields"}).encode()); return
            users=load()
            if phone in users or phone=='dev':
                self.wfile.write(json.dumps({"ok":False,"msg":"User exists"}).encode()); return
            status='pending' if role=='patrol' else 'approved'
            users[phone]={"password":password,"role":role,"status":status,"client_id":f"ZONDI-{phone[-4:]}"}
            save(users)
            self.wfile.write(json.dumps({"ok":True,"role":role,"status":status}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"msg":str(e)}).encode())
    def do_OPTIONS(self):
        self.send_response(200); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
