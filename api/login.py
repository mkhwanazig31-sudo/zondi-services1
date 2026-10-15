from http.server import BaseHTTPRequestHandler
import json, os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_GET(self):
        # If someone opens /login or /api/login directly, serve the login.html file if exists, else return ok
        try:
            # Try to serve login.html from root
            root = os.path.join(os.getcwd(), 'login.html')
            if os.path.exists(root):
                with open(root, 'r', encoding='utf-8') as f:
                    html = f.read()
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write(html.encode())
                return
        except: pass
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps({"ok":True,"msg":"use POST with password zondi@123"}).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get('content-length',0) or 0)
            raw = self.rfile.read(length).decode() if length else '{}'
            body = json.loads(raw or '{}')
        except:
            body = {}
        pwd = str(body.get('password') or body.get('phone') or body.get('email') or '').strip()
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if pwd == "zondi@123":
            self.wfile.write(json.dumps({"ok":True,"role":"dev"}).encode())
        else:
            self.wfile.write(json.dumps({"ok":False,"error":"wrong password"}).encode())
