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
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        length=int(self.headers.get('content-length',0))
        body=json.loads(self.rfile.read(length).decode())
        phone=body.get('phone')
        users=load()
        if phone in users:
            users[phone]["status"]="approved"
            save(users)
        self.wfile.write(json.dumps({"ok":True}).encode())
