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
        self.end_headers()
        length=int(self.headers.get('content-length',0) or 0)
        body=json.loads(self.rfile.read(length).decode() or '{}')
        old_phone=body.get('old_phone')
        new_phone=body.get('new_phone') or old_phone
        users=load()
        if old_phone not in users:
            self.wfile.write(json.dumps({"ok":False}).encode()); return
        u=users[old_phone]
        if body.get('name'): u['name']=body['name']
        if body.get('client_id'): u['client_id']=body['client_id']
        if body.get('role'): u['role']=body['role']
        if body.get('camBrand'): u['camBrand']=body['camBrand']
        if body.get('camId'): u['camId']=body['camId']
        if body.get('camUrl'): u['camUrl']=body['camUrl']
        if new_phone!=old_phone:
            if new_phone in users:
                self.wfile.write(json.dumps({"ok":False,"error":"exists"}).encode()); return
            users[new_phone]=u
            del users[old_phone]
        else:
            users[old_phone]=u
        save(users)
        self.wfile.write(json.dumps({"ok":True}).encode())
