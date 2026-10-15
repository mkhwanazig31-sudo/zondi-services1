import os, json, urllib.request, urllib.parse

KV_URL = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or '').rstrip('/')
KV_TOKEN = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or ''

def kv_get(key):
    if not KV_URL or not KV_TOKEN: return None
    try:
        req = urllib.request.Request(f"{KV_URL}/get/{urllib.parse.quote(key)}", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            val = data.get('result')
            return json.loads(val) if val else None
    except: return None

def kv_set(key, value):
    if not KV_URL or not KV_TOKEN: return False
    try:
        payload = json.dumps(value)
        body = json.dumps(payload).encode()
        req = urllib.request.Request(f"{KV_URL}/set/{urllib.parse.quote(key)}", data=body, headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return True
    except Exception as e:
        print("kv_set failed", e); return False

def get_users(): return kv_get('zondi_users') or {}
def set_users(d): kv_set('zondi_users', json.dumps(d))
def get_pending(): return kv_get('zondi_pending') or {}
def set_pending(d): kv_set('zondi_pending', json.dumps(d))
def get_location(): return kv_get('zondi_location') or {}
def set_location(d): kv_set('zondi_location', json.dumps(d))
