import os, json, urllib.request, urllib.parse
# SAFE - NO EXTERNAL LIBRARY - WILL NEVER CRASH
def get_users():
    try:
        url = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or '').rstrip('/')
        tok = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or ''
        if not url or not tok: return {}
        req = urllib.request.Request(f"{url}/get/zondi_users", headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=4) as r:
            v = json.loads(r.read().decode()).get('result')
            if not v: return {}
            try:
                a=json.loads(v)
                return json.loads(a) if isinstance(a,str) else a
            except: return {}
    except: return {}

def set_users(d):
    try:
        url = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or '').rstrip('/')
        tok = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or ''
        if not url or not tok: return False
        body=json.dumps(json.dumps(d)).encode()
        req=urllib.request.Request(f"{url}/set/zondi_users", data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=4) as r: r.read()
        return True
    except Exception as e:
        print(e); return False

def get_pending():
    try:
        url = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or '').rstrip('/')
        tok = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or ''
        if not url or not tok: return {}
        req = urllib.request.Request(f"{url}/get/zondi_pending", headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=4) as r:
            v = json.loads(r.read().decode()).get('result')
            if not v: return {}
            a=json.loads(v); return json.loads(a) if isinstance(a,str) else a
    except: return {}

def set_pending(d):
    try:
        url = (os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL') or '').rstrip('/')
        tok = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN') or ''
        body=json.dumps(json.dumps(d)).encode()
        req=urllib.request.Request(f"{url}/set/zondi_pending", data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=4) as r: r.read()
        return True
    except: return False

def get_location():
    return {}
def set_location(d): return True
