import logging, datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import schoology, scanner
from .endpoints import ENDPOINTS, CATEGORIES
from .models import GetRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Schoology API Explorer")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
history = []  # in-memory only; never holds credentials

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/endpoints")
def endpoints():
    return {"categories": CATEGORIES, "endpoints": ENDPOINTS}

def _do(path):
    r = schoology.get(path)
    history.append({"timestamp": datetime.datetime.now().isoformat(timespec="seconds"), "method": "GET",
                    "endpoint": path, "status": r["status"], "response_time": r["elapsed_ms"], "response": r})
    return r

@app.post("/api/request")
def do_request(req: GetRequest):
    try:
        schoology.build_url(req.path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _do(req.path)

@app.post("/api/auth-test")
def auth_test():
    r = _do("/v1/users/me")
    b = r["body"] if isinstance(r["body"], dict) else {}
    r["user"] = {"name": b.get("name_display"), "id": b.get("id") or b.get("uid"),
                 "school_id": b.get("school_id"), "role_id": b.get("role_id")} if r["status"] == 200 else None
    return r

@app.get("/api/history")
def get_history():
    return [{k: v for k, v in h.items() if k != "response"} | {"index": i} for i, h in enumerate(history)]

@app.get("/api/history/{i}")
def get_history_item(i: int):
    if not 0 <= i < len(history): raise HTTPException(404, "No such entry")
    return history[i]["response"]

@app.post("/api/scan")
def scan():
    return {"started": scanner.start()}

@app.get("/api/scan/status")
def scan_status():
    return scanner.state
