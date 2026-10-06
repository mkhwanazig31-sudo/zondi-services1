import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = pathlib.Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR))
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/clients", response_class=HTMLResponse)
def clients(request: Request):
    return templates.TemplateResponse("clients.html", {"request": request})

@app.get("/patrol", response_class=HTMLResponse)
def patrol(request: Request):
    return templates.TemplateResponse("patrol.html", {"request": request})

@app.get("/radio", response_class=HTMLResponse)
def radio(request: Request):
    return templates.TemplateResponse("radio.html", {"request": request})
