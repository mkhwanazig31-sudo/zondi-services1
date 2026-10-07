from http.server import BaseHTTPRequestHandler
import json, os
FILE='/tmp/sos.json'
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        body=json.loads(self.rfile.read(int(self.headers.get('content-length',0)).decode() or '{}'))
        arr=[]
        if os.path.exists(FILE):
            try: arr=json.loads(open(FILE).read())
            except: arr=[]
        arr.insert(0,body)
        open(FILE,'w').write(json.dumps(arr[:50]))
        self.wfile.write(json.dumps({"ok":True}).encode())
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
        arr=[]
        if os.path.exists(FILE):
            try: arr=json.loads(open(FILE).read())
            except: arr=[]
        self.wfile.write(json.dumps(arr).encode())
