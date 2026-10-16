from http.server import BaseHTTPRequestHandler
import json, os, time

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN") or "")

def kv_set(key, val, ex=300):
    try:
        import urllib.request
        url = f"{KV_URL}/set/{key}"
        data = json.dumps(val).encode()
        req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type":"application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5).read()
        if ex:
            url2 = f"{KV_URL}/expire/{key}/{ex}"
            req2 = urllib.request.Request(url2, headers={"Authorization": f"Bearer {KV_TOKEN}"}, method="POST")
            urllib.request.urlopen(req2, timeout=5).read()
    except Exception as e:
        print(f"KV set error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        try:
            length = int(self.headers.get('content-length',0) or 0)
            raw = self.rfile.read(length).decode() if length else '{}'
            body = json.loads(raw or '{}')
            
            audio = body.get('audio')
            sender = body.get('from') or body.get('phone') or 'Unknown'
            duration = body.get('duration') or 0
            
            if not audio:
                self.wfile.write(json.dumps({"ok":False,"error":"no audio"}).encode())
                return

            ts_ms = int(time.time()*1000)
            payload = {
                "from": sender,
                "audio": audio,
                "duration": duration,
                "ts": ts_ms,
                "time_str": time.strftime("%H:%M:%S")
            }
            
            # Save latest for all patrols to hear
            kv_set("radio_latest", payload, ex=300)
            kv_set(f"radio:{ts_ms}:{sender}", payload, ex=300)

            self.wfile.write(json.dumps({"ok":True, "ts":ts_ms}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
