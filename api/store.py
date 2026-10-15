import os, json
print("Loading _store.py safe version")
def get_users():
    return {}
def set_users(v):
    print(f"set_users called {len(str(v))} chars")
    return True
def get_pending():
    return {}
def set_pending(v):
    return True
import os
import json
import urllib.request
import urllib.error

KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("KV_REST_API_READ_ONLY_TOKEN") or ""

def _kv_get(key):
    if not KV_URL or not KV_TOKEN:
        print(f"KV not configured for {key}")
        return None
    try:
        url = f"{KV_URL}/get/{key}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            val = data.get("result")
            if val is None:
                return None
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except:
                    return val
            return val
    except Exception as e:
        print(f"_kv_get {key} error: {e}")
        return None

def _kv_set(key, value):
    if not KV_URL or not KV_TOKEN:
        print(f"KV not configured, cannot set {key}")
        return False
    try:
        url = f"{KV_URL}/set/{key}"
        body = json.dumps(value)
        # Vercel KV REST wants value as raw string in body? Use set with value as JSON string
        # Send as POST with value
        payload = json.dumps([body]).encode() if False else json.dumps(value).encode()
        # Simpler: POST to /set/key/value - but we use POST with body
        # Vercel KV: POST /set/mykey with {"value":...} or just value? Use: /set/key/value encoding
        # Most reliable: use url-encoded value
        # We'll use POST to /set/key with value in body
        import urllib.parse
        # Vercel REST: POST https://.../set/key with body = value
        # If value is object, store as JSON string
        store_val = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        req = urllib.request.Request(f"{KV_URL}/set/{key}/{urllib.parse.quote(store_val)}", method="POST", headers={"Authorization": f"Bearer {KV_TOKEN}"})
        # Actually simpler: use set with POST and body
        # Try both methods: first method
        try:
            req2 = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET", key, store_val]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req2, timeout=5) as r2:
                return True
        except:
            # fallback to GET set
            with urllib.request.urlopen(req, timeout=5) as r:
                return True
    except Exception as e:
        print(f"_kv_set {key} error: {e}")
        return False

def get_users():
    v = _kv_get("users")
    return v if isinstance(v, dict) else {}

def set_users(v):
    return _kv_set("users", v)

def get_pending():
    v = _kv_get("pending")
    return v if isinstance(v, dict) else {}

def set_pending(v):
    return _kv_set("pending", v)
