from http.server import BaseHTTPRequestHandler
import json
from _store import get_users

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            users = get_users() or {}
            # if users is still a string (old bad data), try fix
            if isinstance(users, str):
                try: users = json.loads(users)
                except: users = {}
            self.wfile.write(json.dumps(users).encode())
        except Exception as e:
            print("index error", e)
            self.wfile.write(json.dumps({}).encode())

    def do_POST(self): self.do_GET()
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
