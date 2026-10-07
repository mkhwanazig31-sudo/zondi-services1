import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import time

BASE_DIR = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR))
app = FastAPI()

locations = {}

# --- PAGES - EVERY BUTTON NOW HAS A ROUTE ---
@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
@app.get("/registration", response_class=HTMLResponse) # both work
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/clients", response_class=HTMLResponse)
def clients(request: Request):
    return templates.TemplateResponse("clients.html", {"request": request})

@app.get("/patrol", response_class=HTMLResponse)
def patrol(request: Request):
    return templates.TemplateResponse("patrol.html", {"request": request})

@app.get("/dev-portal", response_class=HTMLResponse)
def dev_portal(request: Request):
    return templates.TemplateResponse("dev-portal.html", {"request": request})

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})

# --- TRACKING API ---
@app.post("/update_location")
async def update_location(request: Request):
    data = await request.json()
    user = data.get("user", "anon")
    locations[user] = {
        "lat": float(data["lat"]),
        "lng": float(data["lng"]),
        "time": datetime.now().strftime("%H:%M:%S"),
        "ts": int(time.time()),
        "user": user
    }
    return {"ok": True}

@app.get("/get_clients")
@app.get("/get_locations")
def get_clients():
    return JSONResponse(locations)

@app.post("/verify_qr")
async def verify_qr(request: Request):
    data = await request.json()
    qr = data.get("code", "")
    return {"ok": "ZONDI" in qr.upper(), "msg": qr}
