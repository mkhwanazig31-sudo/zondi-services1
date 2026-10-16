from http.server import BaseHTTPRequestHandler
import json, os

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN") or "")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            import urllib.request
            url = f"{KV_URL}/get/radio_latest"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                result = data.get('result')
                if result:
                    val = json.loads(result) if isinstance(result, str) else result
                    self.wfile.write(json.dumps({"ok":True,"radio":val}).encode())
                    return
            self.wfile.write(json.dumps({"ok":True,"radio":None}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e),"radio":None}).encode())
