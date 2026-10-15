from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            raw = self.rfile.read(int(self.headers.get('content-length',0) or 0)).decode() or '{}'
            body = json.loads(raw)
            pwd = body.get('password') or body.get('devPass') or body.get('dev_pass') or ''
            print(f"Login attempt pwd={pwd}")
            if pwd == 'zondi@123':
                self.wfile.write(json.dumps({"ok":True}).encode())
            else:
                self.wfile.write(json.dumps({"ok":False,"error":"wrong password"}).encode())
        except Exception as e:
            print(e)
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps({"ok":True,"msg":"use POST with password"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
