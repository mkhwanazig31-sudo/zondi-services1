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
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(users).encode())
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
