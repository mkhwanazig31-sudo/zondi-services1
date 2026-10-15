from http.server import BaseHTTPRequestHandler
import json
from _store import get_pending
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            data = get_pending() or {}
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            print(e)
            self.wfile.write(b'{}')
    def do_POST(self): self.do_GET()
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
