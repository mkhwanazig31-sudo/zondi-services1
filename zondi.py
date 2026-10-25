import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import time
BASE_DIR = pathlib.Path(__file__).resolve().parent
app = FastAPI()
locations = {}; sos_alerts = {}; users_db = {}; pending_db = {}; radio_latest = None; stickers_db = {}; scans_db = []
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
    old=locations.get(phone)
    if old and acc > float(old.get("accuracy",100))*1.5 and (int(time.time()*1000)-old.get("timestamp",0))<10000:
        if "emergency" in data:
            old["emergency"]=bool(data.get("emergency")); old["status"]=data.get("status") or "sos"; old["timestamp"]=int(time.time()*1000)
        return {"ok":True,"kept_best":True}
    entry={"phone":phone,"client_id":phone,"lat":lat,"lng":lng,"accuracy":int(acc),"speed":float(data.get("speed") or 0),"heading":float(data.get("heading") or 0),"role":data.get("role") or "client","name":data.get("name") or phone.split("@")[0],"emergency":bool(data.get("emergency") or data.get("sos") or data.get("status")=="sos"),"sos":bool(data.get("emergency") or data.get("sos")),"status":data.get("status") or ("sos" if data.get("emergency") or data.get("sos") else "safe"),"timestamp":int(data.get("timestamp") or time.time()*1000),"ts":int(time.time()),"battery":data.get("battery"),"email":phone}
    locations[phone]=entry
    if entry["emergency"]:
        sos_alerts[phone]={"phone":phone,"lat":lat,"lng":lng,"accuracy":entry["accuracy"],"ts":int(time.time()),"timestamp":entry["timestamp"],"name":entry["name"],"email":phone}
    return {"ok":True,"count":len(locations)}
@app.get("/api/location")
@app.get("/get_locations")
@app.get("/get_clients")
def get_locations(): return JSONResponse(locations)
@app.get("/api/sos")
def get_sos(): return JSONResponse(sos_alerts)
@app.post("/api/sos")
async def post_sos(request: Request):
    data=await request.json(); phone=data.get("phone") or data.get("email") or data.get("client_id"); action=data.get("action")
    if action in ["resolve","clear","stop"] and phone:
        sos_alerts.pop(phone,None)
        if phone in locations: locations[phone].update({"emergency":False,"sos":False,"status":"safe"})
        return {"ok":True}
    if phone and data.get("lat"):
        sos_alerts[phone]={"phone":phone,"lat":float(data["lat"]),"lng":float(data.get("lng") or 0),"accuracy":data.get("accuracy") or "?","ts":int(time.time()),"timestamp":int(time.time()*1000),"name":data.get("name") or phone,"email":phone}
        if phone in locations: locations[phone].update({"emergency":True,"status":"sos"})
    return {"ok":True}
@app.get("/api/index")
def api_index(): return JSONResponse({"users":users_db,"locations":locations})
@app.get("/api/pending")
def get_pending(): return JSONResponse(pending_db)
@app.post("/api/approve")
async def approve(request: Request): d=await request.json(); p=d.get("phone"); 
    if p in pending_db: users_db[p]=pending_db.pop(p); users_db[p]["status"]="active"
    return {"ok":True}
@app.post("/api/delete")
async def delete_user(request: Request): d=await request.json(); p=d.get("phone"); users_db.pop(p,None); pending_db.pop(p,None); locations.pop(p,None); sos_alerts.pop(p,None); return {"ok":True}
@app.post("/api/notify-family")
async def notify_family(request: Request): return {"ok":True}
@app.post("/api/radio")
async def radio_post(request: Request): global radio_latest; d=await request.json(); radio_latest={"from":d.get("from"),"audio":d.get("audio"),"ts":int(time.time()*1000)}; return {"ok":True}
@app.get("/api/radio-latest")
def radio_latest_get(): return JSONResponse({"radio":radio_latest})
@app.post("/api/stickers")
@app.get("/api/stickers")
async def stickers_api(request: Request):
    if request.method=="GET": return JSONResponse(stickers_db)
    d=await request.json()
    if d.get("action")=="updateStatus": sid=d.get("id"); 
        if sid in stickers_db: stickers_db[sid].update({"status":d.get("status")})
    else: sid=d.get("id") or f"STK-{int(time.time())}"; stickers_db[sid]=d; stickers_db[sid]["id"]=sid
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
def debug(): return {"locations":len(locations),"sos":len(sos_alerts),"users":len(users_db),"keys":list(locations.keys())[:3]}
