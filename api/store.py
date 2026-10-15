import os, json, urllib.request, urllib.parse
KV_URL = (os.environ.get("KV_REST_API_URL") or os.environ.get("KV_URL") or "").rstrip("/")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or ""
def _get(k):
    if not KV_URL or not KV_TOKEN: return None
    try:
        url = f"{KV_URL}/get/{k}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read().decode())
            v = d.get("result")
            if isinstance(v, str):
                try: return json.loads(v)
                except: return v
            return v
    except Exception as e:
        print(e); return None
def _set(k, v):
    if not KV_URL or not KV_TOKEN: return False
    try:
        sv = json.dumps(v)
        req = urllib.request.Request(f"{KV_URL}", data=json.dumps(["SET", k, sv]).encode(), headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return True
    except Exception as e:
        print(e); return False
def get_users():
    x=_get("users"); return x if isinstance(x, dict) else {}
def set_users(v): return _set("users", v)
def get_pending():
    x=_get("pending"); return x if isinstance(x, dict) else {}
def set_pending(v): return _set("pending", v)
