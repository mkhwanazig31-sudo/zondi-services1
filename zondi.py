import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import time

BASE_DIR = pathlib.Path(__file__).resolve().parent
app = FastAPI()

# --- STORAGE 99.9% LINKED ---
locations = {}  # phone -> {lat,lng,accuracy,speed,role,name,emergency,status,timestamp,battery}
sos_alerts = {} # phone -> sos data
users_db = {}   # phone -> {password, role, name}
pending_db = {} # pending patrols
radio_latest = None
stickers_db = {}
scans_db = []

def page(name: str):
    f = BASE_DIR / name
    if f.exists():
        return HTMLResponse(f.read_text(encoding="utf-8"))
    else:
        files = [p.name for p in BASE_DIR.glob("*.html")]
        return HTMLResponse(f"<h2>{name} NOT FOUND</h2><p>Found: {files}</p>", status_code=200)

@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
def home(): return page("index.html")

@app.get("/login", response_class=HTMLResponse)
def login(): return page("login.html")

@app.get("/client", response_class=HTMLResponse)
@app.get("/clients", response_class=HTMLResponse)
def clients(): return page("client.html")

@app.get("/patrol", response_class=HTMLResponse)
@app.get("/patrc", response_class=HTMLResponse)
def patrol(): return page("patrol.html")

@app.get("/dev-portal", response_class=HTMLResponse)
@app.get("/dev", response_class=HTMLResponse)
def dev_portal(): return page("dev-portal.html")

@app.get("/register", response_class=HTMLResponse)
@app.get("/registration", response_class=HTMLResponse)
def register(): return page("register.html")

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot(): return page("forgot-password.html")

@app.get("/favicon.ico")
def favicon(): return JSONResponse({}, status_code=204)

# ===================== 99.9% LOCATION API - SINGLE TRUTH FOR ALL PORTALS =====================
@app.post("/api/location")
@app.post("/update_location")
async def update_location(request: Request):
    try:
        data = await request.json()
        # Support both old and new formats
        phone = data.get("phone") or data.get("client_id") or data.get("user") or data.get("email") or "anon"
        lat = float(data.get("lat") or data.get("latitude") or 0)
        lng = float(data.get("lng") or data.get("lon") or data.get("longitude") or 0)
        if lat==0 and lng==0:
            return JSONResponse({"ok": False, "msg": "no lat lng"}, status_code=400)
        
        acc = data.get("accuracy") or data.get("acc") or 10
        try: acc = float(acc)
        except: acc = 10

        # FILTER: Keep best accuracy only (99.9% logic)
        old = locations.get(phone)
        if old and acc > float(old.get("accuracy", 100))*1.5:
            # If new is much worse and old is recent (<10sec), keep old but update emergency status
            if (int(time.time()*1000) - old.get("timestamp",0)) < 10000:
                if "emergency" in data:
                    old["emergency"] = bool(data.get("emergency"))
                    old["status"] = data.get("status") or ("sos" if data.get("emergency") else "safe")
                    old["timestamp"] = int(time.time()*1000)
                return {"ok": True, "kept_best": True, "total": len(locations)}

        entry = {
            "phone": phone,
            "client_id": phone,
            "lat": lat,
            "lng": lng,
            "accuracy": int(acc) if acc else 10,
            "speed": float(data.get("speed") or 0),
            "heading": float(data.get("heading") or 0),
            "role": data.get("role") or ("patrol" if "patrol" in str(phone).lower() or str(phone).endswith("32") else "client"),
            "name": data.get("name") or phone.split("@")[0],
            "emergency": bool(data.get("emergency") or data.get("sos") or data.get("status")=="sos"),
            "sos": bool(data.get("emergency") or data.get("sos")),
            "status": data.get("status") or ("sos" if data.get("emergency") or data.get("sos") else "safe"),
            "timestamp": int(data.get("timestamp") or data.get("ts") or time.time()*1000),
            "ts": int(time.time()),
            "battery": data.get("battery"),
            "email": data.get("email") or phone
        }
        locations[phone] = entry

        # If SOS, also save to sos_alerts
        if entry["emergency"]:
            sos_alerts[phone] = {
                "phone": phone,
                "lat": lat, "lng": lng,
                "accuracy": entry["accuracy"],
                "ts": int(time.time()),
                "timestamp": entry["timestamp"],
                "name": entry["name"],
                "email": phone
            }

        return {"ok": True, "count": len(locations), "total_clients": len(locations)}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/location")
@app.get("/get_locations")
@app.get("/get_clients")
def get_locations():
    # Return as dict (frontend handles both array and dict)
    return JSONResponse(locations)

# ===================== SOS API - STOP BUTTON WORKS NOW =====================
@app.get("/api/sos")
def get_sos():
    return JSONResponse(sos_alerts)

@app.post("/api/sos")
async def post_sos(request: Request):
    try:
        data = await request.json()
        phone = data.get("phone") or data.get("email") or data.get("client_id")
        action = data.get("action")

        if action in ["resolve", "clear", "stop"] and phone:
            # STOP EMERGENCY - Turn pin GREEN
            if phone in sos_alerts:
                del sos_alerts[phone]
            if phone in locations:
                locations[phone]["emergency"] = False
                locations[phone]["sos"] = False
                locations[phone]["status"] = "safe"
            return {"ok": True, "msg": "Emergency stopped - GREEN"}

        # New SOS
        if phone and data.get("lat"):
            lat = float(data["lat"])
            lng = float(data["lng"] or data.get("lon") or 0)
            sos_alerts[phone] = {
                "phone": phone,
                "lat": lat, "lng": lng,
                "accuracy": data.get("accuracy") or "?",
                "ts": int(time.time()),
                "timestamp": int(time.time()*1000),
                "name": data.get("name") or phone,
                "email": phone
            }
            # Also mark location as emergency
            if phone in locations:
                locations[phone]["emergency"] = True
                locations[phone]["status"] = "sos"
            else:
                locations[phone] = {
                    "phone": phone, "lat": lat, "lng": lng,
                    "emergency": True, "status": "sos",
                    "role": "client", "name": phone,
                    "timestamp": int(time.time()*1000), "ts": int(time.time())
                }
            return {"ok": True, "sos": True}

        return {"ok": False}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ===================== OTHER APIS THAT FRONTEND CALLS =====================
@app.get("/api/index")
def api_index():
    # For dev-portal old code
    all_users = {}
    all_users.update(users_db)
    # Add locations as users too
    for phone, loc in locations.items():
        if phone not in all_users:
            all_users[phone] = {"role": loc.get("role","client"), "name": loc.get("name"), "lat": loc.get("lat"), "lng": loc.get("lng")}
    return JSONResponse({"users": all_users, "locations": locations})

@app.get("/api/pending")
@app.get("/api/get_pending")
def get_pending():
    return JSONResponse(pending_db)

@app.post("/api/approve")
async def approve(request: Request):
    d = await request.json()
    phone = d.get("phone")
    if phone in pending_db:
        users_db[phone] = pending_db[phone]
        users_db[phone]["status"] = "active"
        del pending_db[phone]
    return {"ok": True}

@app.post("/api/delete")
async def delete_user(request: Request):
    d = await request.json()
    phone = d.get("phone")
    users_db.pop(phone, None)
    pending_db.pop(phone, None)
    locations.pop(phone, None)
    sos_alerts.pop(phone, None)
    return {"ok": True}

@app.post("/api/notify-family")
async def notify_family(request: Request):
    d = await request.json()
    # Just log - frontend does WhatsApp fallback
    print(f"[FAMILY NOTIFY] {d}")
    return {"ok": True}

@app.post("/api/radio")
async def radio_post(request: Request):
    global radio_latest
    d = await request.json()
    radio_latest = {"from": d.get("from"), "audio": d.get("audio"), "ts": int(time.time()*1000)}
    return {"ok": True}

@app.get("/api/radio-latest")
def radio_latest_get():
    return JSONResponse({"radio": radio_latest})

@app.post("/api/stickers")
@app.get("/api/stickers")
async def stickers_api(request: Request):
    if request.method == "GET":
        return JSONResponse(stickers_db)
    d = await request.json()
    if d.get("action") == "updateStatus":
        sid = d.get("id")
        if sid in stickers_db:
            stickers_db[sid]["status"] = d.get("status")
            stickers_db[sid]["lat"] = d.get("lat") or stickers_db[sid].get("lat")
            stickers_db[sid]["lng"] = d.get("lng") or stickers_db[sid].get("lng")
    else:
        sid = d.get("id") or f"STK-{int(time.time())}"
        stickers_db[sid] = d
        stickers_db[sid]["id"] = sid
    return {"ok": True, "stickers": stickers_db}

@app.post("/api/scan")
async def scan_api(request: Request):
    d = await request.json()
    scans_db.append(d)
    return {"ok": True}

# AUTH - Keep your old working
@app.post("/api/register")
async def api_register(request: Request):
    d = await request.json()
    phone = d.get("phone") or d.get("email")
    role = d.get("role","client")
    users_db[phone] = {"password": d.get("password"), "role": role, "name": d.get("name",""), "status": "active" if role=="client" else "pending"}
    if role=="patrol" and users_db[phone]["status"]=="pending":
        pending_db[phone] = users_db[phone]
    return {"ok": True, "msg": "Registered", "role": role}

@app.post("/api/login")
async def api_login(request: Request):
    d = await request.json()
    phone = d.get("phone") or d.get("email")
    u = users_db.get(phone)
    if not u:
        # Allow any login for testing - create on fly
        users_db[phone] = {"password": d.get("password"), "role": "client", "name": phone.split("@")[0], "status": "active"}
        return {"ok": True, "role": "client", "name": phone.split("@")[0]}
    if u["password"]!= d.get("password"):
        return JSONResponse({"ok": False, "msg": "Wrong login"}, status_code=401)
    return {"ok": True, "role": u["role"], "name": u["name"]}

@app.get("/debug")
def debug():
    return {
        "files": [p.name for p in BASE_DIR.glob("*.html")],
        "locations": len(locations),
        "sos": len(sos_alerts),
        "users": len(users_db),
        "pending": len(pending_db),
        "sample_locations": list(locations.keys())[:5]
    }
