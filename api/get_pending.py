from http.server import BaseHTTPRequestHandler
import json, os
FILE='/tmp/zondi_users.json'
def load():
    if not os.path.exists(FILE): return {}
    try:
        with open(FILE,'r') as f: return json.load(f)
    except: return {}
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        users=load()
        pending=[{"phone":k,"role":v["role"],"status":v["status"]} for k,v in users.items() if v["status"]=="pending"]
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        self.wfile.write(json.dumps(pending).encode())
