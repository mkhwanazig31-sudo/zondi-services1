import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time, os, json
BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- KV SETUP - BEST WAY TO KEEP MEMORY IF ONE FAILS ---
USE_KV = False
kv_client = None
try:
    # Vercel KV via REST - If you have KV_REST_API_URL and TOKEN in Vercel Env
    from vercel_kv import kv as vercel_kv
    # test
    vercel_kv.set("test", "1")
    USE_KV = True
    kv_client = vercel_kv
    print("✅ KV CONNECTED")
except Exception as e:
    try:
        # Fallback: Upstash REST
        import upstash_redis
        # Will auto use env vars UPSTASH_REDIS_REST_URL / TOKEN
        from upstash_redis import Redis
        kv_client = Redis.from_env()
        kv_client.set("test","1")
        USE_KV = True
        print("✅ UPSTASH KV CONNECTED")
    except Exception as e2:
        print(f"⚠️ KV NOT FOUND, USING MEMORY ONLY: {e} / {e2}")
        USE_KV = False

app = FastAPI()
# BUG 1 FIX - CORS - Allow phone, laptop, all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fallback memory
locations = {}; sos_alerts = {}; users_db = {}; pending_db = {}; radio_latest = None; stickers_db = {}; scans_db = []

# --- KV HELPERS - KEEP MEMORY IF ONE FAILS ---
def kv_hgetall(key):
    if not USE_KV: return None
    try:
        data = kv_client.hgetall(key)
        if not data: return {}
        out = {}
        for k,v in data.items():
            try: out[k] = json.loads(v) if isinstance(v, str) else v
            except: out[k] = v
        return out
    except: return None

def kv_hget(key, field):
    if not USE_KV: return None
    try:
        v = kv_client.hget(key, field)
        if not v: return None
        try: return json.loads(v) if isinstance(v, str) else v
        except: return v
    except: return None

def kv_hset(key, field, value):
    if not USE_KV: return False
    try:
        kv_client.hset(key, field, json.dumps(value) if isinstance(value, dict) else value)
        return True
    except: return False

def kv_hdel(key, field):
    if not USE_KV: return False
    try: kv_client.hdel(key, field); return True
    except: return False

def kv_set(key, value):
    if not USE_KV: return False
    try: kv_client.set(key, json.dumps(value)); return True
    except: return False

def kv_get(key):
    if not USE_KV: return None
    try:
        v = kv_client.get(key)
        if not v: return None
        try: return json.loads(v) if isinstance(v, str) else v
        except: return v
    except: return None

def page(n):
    f=BASE_DIR/n
    return HTMLResponse(f.read_text(encoding="utf-8")) if f.exists() else HTMLResponse(f"<h2>{n} NOT FOUND</h2>",status_code=404)

@app.get("/")
@app.get("/home")
def home(): return page("index.html")
@app.get("/login")
def login(): return page("login.html")
@app.get("/client")
@app.get("/clients")
def clients(): return page("client.html")
@app.get("/patrol")
@app.get("/patrc")
def patrol(): return page("patrol.html")
@app.get("/dev-portal")
@app.get("/dev")
def dev_portal(): return page("dev-portal.html")
@app.get("/register")
def register(): return page("register.html")
@app.get("/forgot-password")
def forgot(): return page("forgot-password.html")
@app.get("/favicon.ico")
def favicon(): return JSONResponse({},status_code=204)

@app.post("/api/location")
@app.post("/update_location")
async def update_location(request: Request):
    data=await request.json()
    phone=data.get("phone") or data.get("client_id") or data.get("user") or data.get("email") or "anon"
    lat=float(data.get("lat") or 0); lng=float(data.get("lng") or data.get("lon") or data.get("longitude") or 0)
    if lat==0: return JSONResponse({"ok":False},status_code=400)
    acc=float(data.get("accuracy") or data.get("acc") or 10)
    
    # BUG 2 - Get old from KV first, fallback to memory
    old = kv_hget("zondi_locations", phone) if USE_KV else locations.get(phone)
    if old is None and USE_KV: old = locations.get(phone) # second fallback
    
    if old and acc > float(old.get("accuracy",100))*1.5 and (int(time.time()*1000)-int(old.get("timestamp",0)))<10000:
        if "emergency" in data:
            old["emergency"]=bool(data.get("emergency")); old["status"]=data.get("status") or "sos"; old["timestamp"]=int(time.time()*1000)
            if USE_KV: kv_hset("zondi_locations", phone, old)
            else: locations[phone]=old
        return {"ok":True,"kept_best":True,"kv":USE_KV}
    
    # BUG 3 - ROLE DETECT - Patrol vs Client
    raw_role = (data.get("role") or "").lower()
    phone_lower = phone.lower()
    if raw_role in ["patrol","admin","security","officer"]:
        role_final = "patrol"
    elif "patrol" in phone_lower or phone_lower.endswith("32") or "sec" in phone_lower or "officer" in phone_lower:
        role_final = "patrol"
    else:
        role_final = "client"
    
    entry={"phone":phone,"client_id":phone,"lat":lat,"lng":lng,"accuracy":int(acc),"speed":float(data.get("speed") or 0),"heading":float(data.get("heading") or 0),"role":role_final,"name":data.get("name") or phone.split("@")[0],"emergency":bool(data.get("emergency") or data.get("sos") or data.get("status")=="sos"),"sos":bool(data.get("emergency") or data.get("sos")),"status":data.get("status") or ("sos" if data.get("emergency") or data.get("sos") else "safe"),"timestamp":int(data.get("timestamp") or time.time()*1000),"ts":int(time.time()),"battery":data.get("battery"),"email":phone}
    
    # BUG 2 - Save to BOTH KV and Memory - If KV fails, memory keeps it
    if USE_KV:
        kv_hset("zondi_locations", phone, entry)
    locations[phone]=entry # Always save memory too
    
    if entry["emergency"]:
        sos_entry={"phone":phone,"lat":lat,"lng":lng,"accuracy":entry["accuracy"],"ts":int(time.time()),"timestamp":entry["timestamp"],"name":entry["name"],"email":phone}
        if USE_KV: kv_hset("zondi_sos", phone, sos_entry)
        sos_alerts[phone]=sos_entry
    
    return {"ok":True,"count":len(locations),"kv":USE_KV,"role":role_final}

@app.get("/api/location")
@app.get("/get_locations")
@app.get("/get_clients")
def get_locations():
    # BUG 2 - Get from KV, merge with memory
    if USE_KV:
        kv_data = kv_hgetall("zondi_locations")
        if kv_data:
            # merge memory too
            merged = {**kv_data, **locations}
            return JSONResponse(merged)
    return JSONResponse(locations)

@app.get("/api/sos")
def get_sos():
    if USE_KV:
        kv_data = kv_hgetall("zondi_sos")
        if kv_data: return JSONResponse({**kv_data, **sos_alerts})
    return JSONResponse(sos_alerts)

@app.post("/api/sos")
async def post_sos(request: Request):
    data=await request.json(); phone=data.get("phone") or data.get("email") or data.get("client_id"); action=data.get("action")
    if action in ["resolve","clear","stop"] and phone:
        if USE_KV: kv_hdel("zondi_sos", phone)
        sos_alerts.pop(phone,None)
        if USE_KV:
            old = kv_hget("zondi_locations", phone)
            if old: old.update({"emergency":False,"sos":False,"status":"safe"}); kv_hset("zondi_locations", phone, old)
        if phone in locations: locations[phone].update({"emergency":False,"sos":False,"status":"safe"})
        return {"ok":True,"kv":USE_KV}
    if phone and data.get("lat"):
        sos_entry={"phone":phone,"lat":float(data["lat"]),"lng":float(data.get("lng") or 0),"accuracy":data.get("accuracy") or "?","ts":int(time.time()),"timestamp":int(time.time()*1000),"name":data.get("name") or phone,"email":phone}
        if USE_KV: kv_hset("zondi_sos", phone, sos_entry)
        sos_alerts[phone]=sos_entry
        if USE_KV:
            old = kv_hget("zondi_locations", phone)
            if old: old.update({"emergency":True,"status":"sos"}); kv_hset("zondi_locations", phone, old)
        if phone in locations: locations[phone].update({"emergency":True,"status":"sos"})
    return {"ok":True,"kv":USE_KV}

@app.get("/api/index")
def api_index(): 
    locs = kv_hgetall("zondi_locations") if USE_KV else None
    return JSONResponse({"users":users_db,"locations":locs or locations,"kv":USE_KV})
@app.get("/api/pending")
def get_pending(): return JSONResponse(pending_db)
@app.post("/api/approve")
async def approve(request: Request): 
    d=await request.json(); p=d.get("phone")
    if p in pending_db:
        users_db[p]=pending_db.pop(p); users_db[p]["status"]="active"
    return {"ok":True}
@app.post("/api/delete")
async def delete_user(request: Request): d=await request.json(); p=d.get("phone"); users_db.pop(p,None); pending_db.pop(p,None); locations.pop(p,None); sos_alerts.pop(p,None); 
    if USE_KV: kv_hdel("zondi_locations", p); kv_hdel("zondi_sos", p)
    return {"ok":True}
@app.post("/api/notify-family")
async def notify_family(request: Request): return {"ok":True}
@app.post("/api/radio")
async def radio_post(request: Request): 
    global radio_latest; d=await request.json(); radio_latest={"from":d.get("from"),"audio":d.get("audio"),"ts":int(time.time()*1000)}; 
    if USE_KV: kv_set("zondi_radio", radio_latest)
    return {"ok":True}
@app.get("/api/radio-latest")
def radio_latest_get(): 
    if USE_KV:
        r=kv_get("zondi_radio")
        if r: return JSONResponse({"radio":r})
    return JSONResponse({"radio":radio_latest})
@app.post("/api/stickers")
@app.get("/api/stickers")
async def stickers_api(request: Request):
    if request.method=="GET": return JSONResponse(stickers_db)
    d=await request.json()
    if d.get("action")=="updateStatus": 
        sid=d.get("id")
        if sid in stickers_db: stickers_db[sid].update({"status":d.get("status")})
    else: 
        sid=d.get("id") or f"STK-{int(time.time())}"; stickers_db[sid]=d; stickers_db[sid]["id"]=sid
    return {"ok":True}
@app.post("/api/scan")
async def scan_api(request: Request): scans_db.append(await request.json()); return {"ok":True}
@app.post("/api/register")
async def api_register(request: Request): d=await request.json(); phone=d.get("phone") or d.get("email"); role=d.get("role","client"); users_db[phone]={"password":d.get("password"),"role":role,"name":d.get("name",""),"status":"active" if role=="client" else "pending"}; 
    if role=="patrol" and users_db[phone]["status"]=="pending": pending_db[phone]=users_db[phone]
    return {"ok":True}
@app.post("/api/login")
async def api_login(request: Request): d=await request.json(); phone=d.get("phone") or d.get("email"); u=users_db.get(phone); 
    if not u: users_db[phone]={"password":d.get("password"),"role":"client","name":phone.split("@")[0],"status":"active"}; return {"ok":True,"role":"client"}
    if u["password"]!=d.get("password"): return JSONResponse({"ok":False},status_code=401)
    return {"ok":True,"role":u["role"]}
@app.get("/debug")
def debug(): 
    kv_info = kv_hgetall("zondi_locations") if USE_KV else None
    return {"kv_enabled":USE_KV,"locations_mem":len(locations),"locations_kv":len(kv_info) if kv_info else 0,"sos":len(sos_alerts),"users":len(users_db),"keys":list((kv_info or locations).keys())[:3]}
