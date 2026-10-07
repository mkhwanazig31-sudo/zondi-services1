from http.server import BaseHTTPRequestHandler
import json
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        length=int(self.headers.get('content-length',0))
        body=json.loads(self.rfile.read(length).decode())
        pwd=body.get('password','').strip()
        # DEV = ONLY password, no phone
        if pwd=='zondi@123':
            self.wfile.write(json.dumps({"ok":True,"role":"dev","client_id":"CONTROL"}).encode()); return
        # for client/patrol we let frontend handle for now
        self.wfile.write(json.dumps({"ok":True,"role":body.get('role','client'),"client_id":body.get('phone')}).encode())
