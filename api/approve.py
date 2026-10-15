from http.server import BaseHTTPRequestHandler
import json, os

USERS='/tmp/zondi_users.json'
PENDING='/tmp/zondi_pending.json'

def load(f):
    if not os.path.exists(f): return {}
    try:
        with open(f,'r') as fp: return json.load(fp)
    except: return {}
def save(f,d):
    try:
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f,'w') as fp: json.dump(fp,d) if False else json.dump(d,fp)
    except: pass

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
        phone=(body.get('phone') or '').strip()

        users=load(USERS)
        pending=load(PENDING)

        # RULE: JUST APPROVE - check both places
        if phone in pending:
            users[phone] = {**pending[phone], "status":"active"}
            del pending[phone]
            save(PENDING, pending)
            save(USERS, users)
            self.wfile.write(json.dumps({"ok":True,"phone":phone,"status":"active","from":"pending"}).encode())
            return

        if phone in users:
            users[phone]["status"]="active"
            save(USERS, users)
            self.wfile.write(json.dumps({"ok":True,"phone":phone,"status":"active"}).encode())
            return

        self.wfile.write(json.dumps({"ok":False,"error":"not found"}).encode())
