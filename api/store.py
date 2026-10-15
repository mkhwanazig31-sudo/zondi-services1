import os, json
try:
    from upstash_redis import Redis
    url = os.getenv('KV_REST_API_URL') or os.getenv('STORAGE_REST_API_URL')
    token = os.getenv('KV_REST_API_TOKEN') or os.getenv('STORAGE_REST_API_TOKEN')
    redis = Redis(url=url, token=token)
    USE_KV = True
except:
    USE_KV = False
    redis = None

def get_users():
    if not USE_KV: return {}
    d = redis.get('zondi_users')
    return json.loads(d) if d else {}

def set_users(d):
    if USE_KV: redis.set('zondi_users', json.dumps(d))

def get_pending():
    if not USE_KV: return {}
    d = redis.get('zondi_pending')
    return json.loads(d) if d else {}

def set_pending(d):
    if USE_KV: redis.set('zondi_pending', json.dumps(d))

def get_location():
    if not USE_KV: return {}
    d = redis.get('zondi_location')
    return json.loads(d) if d else {}

def set_location(d):
    if USE_KV: redis.set('zondi_location', json.dumps(d))
