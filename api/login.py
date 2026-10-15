from http.server import BaseHTTPRequestHandler
import json
class handler(BaseHTTPRequestHandler):
 def do_POST(self):
  self.send_response(200)
  self.send_header('Content-type','application/json')
  self.send_header('Access-Control-Allow-Origin','*')
  self.end_headers()
  try:
   body=json.loads(self.rfile.read(int(self.headers.get('content-length',0) or 0)).decode() or '{}')
   pwd=body.get('password') or ''
   if pwd=='zondi@123':
    self.wfile.write(b'{"ok":true}')
   else:
    self.wfile.write(b'{"ok":false}')
  except Exception as e:
   self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
 def do_GET(self):
  self.send_response(200)
  self.send_header('Content-type','application/json')
  self.send_header('Access-Control-Allow-Origin','*')
  self.end_headers()
  self.wfile.write(b'{"ok":true,"msg":"login works"}')
 def do_OPTIONS(self):
  self.send_response(200)
  self.send_header('Access-Control-Allow-Origin','*')
  self.send_header('Access-Control-Allow-Methods','POST, GET, OPTIONS')
  self.send_header('Access-Control-Allow-Headers','Content-Type')
  self.end_headers()
