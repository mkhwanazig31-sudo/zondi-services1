from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN") or ""
PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID") or ""
# FREE Alternative - UltraMsg / CallMeBot
ULTRAMSG_INSTANCE = os.environ.get("ULTRAMSG_INSTANCE") or ""
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN") or ""

KV_URL = (os.environ.get("KV_REST_API_URL") or "").rstrip("/")
KV_TOKEN = (os.environ.get("KV_REST_API_TOKEN") or "")

def send_whatsapp_cloud(to, message):
    """Meta WhatsApp Cloud API - TRUE auto-send"""
    if not WHATSAPP_TOKEN or not PHONE_ID:
        return False, "No WHATSAPP_TOKEN"
    try:
        url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            res = r.read().decode()
            print(f"WA Cloud sent to {to}: {res}")
            return True, res
    except Exception as e:
        print(f"WA Cloud error {to}: {e}")
        return False, str(e)

def send_ultramsg(to, message):
    """UltraMsg - easier, works with normal WhatsApp"""
    if not ULTRAMSG_INSTANCE or not ULTRAMSG_TOKEN:
        return False, "No UltraMsg"
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
        data = urllib.parse.urlencode({
            "token": ULTRAMSG_TOKEN,
            "to": to,
            "body": message
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            res = r.read().decode()
            print(f"UltraMsg sent to {to}: {res}")
            return True, res
    except Exception as e:
        print(f"UltraMsg error: {e}")
        return False, str(e)

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
            length=int(self.headers.get('content-length',0) or 0)
            body=json.loads((self.rfile.read(length).decode() if length else '{}') or '{}')
            
            family = body.get('family') or []
            lat = body.get('lat')
            lng = body.get('lng')
            acc = body.get('accuracy') or body.get('acc') or '?'
            sender = body.get('phone') or body.get('sender') or 'Client'
            is_test = body.get('test') or False

            if not family:
                self.wfile.write(json.dumps({"ok":False,"error":"No family"}).encode())
                return

            if lat and lng:
                maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                if is_test:
                    msg = f"📍 ZONDI Location Garankuwa from {sender}\n{maps_link}\n±{acc}m - Test"
                else:
                    msg = f"🚨 ZONDI SOS Garankuwa! HELP! from {sender}!\n📍 {maps_link}\n±{acc}m\n🚔 Call 10111 if no response!"
            else:
                msg = f"🚨 ZONDI SOS Garankuwa from {sender}! HELP!"

            results=[]
            for f in family:
                to = f.get('phone') if isinstance(f, dict) else f
                # Clean number
                to = str(to).replace('+','').replace(' ','')
                if to.startswith('0'): to='27'+to[1:]
                if not to.startswith('27'): to='27'+to

                # Try Cloud API first, then UltraMsg
                ok, res = send_whatsapp_cloud(to, msg)
                if not ok:
                    ok, res = send_ultramsg(to, msg)
                
                results.append({"to":to, "ok":ok, "res":res})

            self.wfile.write(json.dumps({"ok":True, "sent":results, "message":msg}).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"ok":False,"error":str(e)}).encode())
