from http.server import BaseHTTPRequestHandler
import json
from _store import get_users
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        users=get_users()
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(users).encode())
    def do_POST(self): self.do_GET()
