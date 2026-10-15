import os, json, urllib.request, urllib.parse

KV_URL = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or os.getenv('KV_URL') or '').rstrip('/')
KV_TOKEN = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or os.getenv('KV_REST_API_TOKEN') or ''

def _kv_get(key):
    if not KV_URL or not KV_TOKEN:
        print("KV missing env")
        return None
    try:
        url = f"{KV_URL}/get/{urllib.parse.quote(key)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
            val = data.get('result')
            if val is None:
                return None
            # Upstash returns JSON string - may be double encoded
            if isinstance(val, str):
                try:
                    # try parse, if still string, parse again
                    first = json.loads(val)
                    if isinstance(first, str):
                        return json.loads(first)
                    return first
                except:
                    return json.loads(val) if val.startswith('{') or val.startswith('[') else val
            return val
    except Exception as e:
        print("kv_get fail", e)
        return None

def _kv_set(key, obj):
    if not KV_URL or not KV_TOKEN:
        print("KV missing env on set")
        return False
    try:
        # Store obj as JSON string ONCE
        payload = json.dumps(obj)
        # Upstash REST expects body to be JSON string of the value
        body = json.dumps(payload).encode()
        url = f"{KV_URL}/set/{urllib.parse.quote(key)}"
        req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            r.read()
            return True
    except Exception as e:
        print("kv_set fail", e)
        return False

def get_users(): return _kv_get('zondi_users') or {}
def set_users(d): _kv_set('zondi_users', d)
def get_pending(): return _kv_get('zondi_pending') or {}
def set_pending(d): _kv_set('zondi_pending', d)
def get_location(): return _kv_get('zondi_location') or {}
def set_location(d): _kv_set('zondi_location', d)
