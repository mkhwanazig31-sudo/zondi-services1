import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import time

BASE_DIR = pathlib.Path(__file__).resolve().parent
app = FastAPI()
locations = {}

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

@app.get("/register", response_class=HTMLResponse)
@app.get("/registration", response_class=HTMLResponse)
def register(): return page("register.html")

@app.get("/clients", response_class=HTMLResponse)
def clients(): return page("clients.html")

@app.get("/patrol", response_class=HTMLResponse)
def patrol(): return page("patrol.html")

@app.get("/dev-portal", response_class=HTMLResponse)
def dev_portal(): return page("dev-portal.html")

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot(): return page("forgot-password.html")

@app.get("/favicon.ico")
def favicon(): return JSONResponse({}, status_code=204)

# API
@app.post("/update_location")
async def update_location(request: Request):
    data = await request.json()
    user = data.get("user", "anon")
    locations[user] = {"lat": float(data["lat"]), "lng": float(data["lng"]), "time": datetime.now().strftime("%H:%M:%S"), "ts": int(time.time()), "user": user}
    return {"ok": True}

@app.get("/get_clients")
@app.get("/get_locations")
def get_clients(): return JSONResponse(locations)

@app.post("/verify_qr")
async def verify_qr(request: Request):
    d = await request.json()
    return {"ok": True, "code": d.get("code")}

@app.get("/debug")
def debug():
    return {"files": [p.name for p in BASE_DIR.glob("*.html")]}
