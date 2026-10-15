from http.server import BaseHTTPRequestHandler
import json
from _store import get_pending
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p=get_pending()
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(p).encode())
    def do_POST(self): self.do_GET()
