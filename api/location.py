from http.server import BaseHTTPRequestHandler
import json
from _store import get_location, set_location
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            self.wfile.write(json.dumps(get_location() or {}).encode())
        except:
            self.wfile.write(b'{}')
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            b=json.loads(self.rfile.read(int(self.headers.get('content-length',0) or 0)).decode() or '{}')
            key=(b.get('phone') or b.get('email') or 'unknown').strip().lower()
            loc=get_location() or {}
            loc[key]={"lat":float(b.get('lat',0)),"lng":float(b.get('lng',0)),"time":b.get('time','')}
            set_location(loc)
            self.wfile.write(json.dumps({"ok":True}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
