from http.server import BaseHTTPRequestHandler
import json, os, time
FILE='/tmp/locs.json'
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        body=json.loads(self.rfile.read(int(self.headers.get('content-length',0))).decode())
        locs={}
        if os.path.exists(FILE):
            try: locs=json.loads(open(FILE).read())
            except: locs={}
        locs[body.get('client_id','unknown')]=body
        open(FILE,'w').write(json.dumps(locs))
        self.wfile.write(json.dumps({"ok":True}).encode())
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        locs={}
        if os.path.exists(FILE):
            try: locs=json.loads(open(FILE).read())
            except: pass
        self.wfile.write(json.dumps(locs).encode())
