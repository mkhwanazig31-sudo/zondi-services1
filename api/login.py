from http.server import BaseHTTPRequestHandler
import json
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers.get('content-length',0) or 0)).decode() or '{}')
        pwd=(body.get('password') or body.get('phone') or body.get('email') or '').strip()
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        # ONLY PASSWORD - no email
        if pwd == "zondi@123":
            self.wfile.write(json.dumps({"ok":True,"role":"dev"}).encode())
        else:
            self.wfile.write(json.dumps({"ok":False,"error":"wrong password"}).encode())
