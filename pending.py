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
            self.wfile.write(json.dumps(get_pending() or {}).encode())
        except:
            self.wfile.write(b'{}')
    def do_POST(self): self.do_GET()
