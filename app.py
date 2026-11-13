import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core import jobs, worker

app = FastAPI(title="crackdex")
TOKEN = os.getenv("APP_TOKEN", "")


def auth(request: Request):
    if not TOKEN:
        return
    supplied = request.headers.get("x-token") or request.query_params.get("token")
    if supplied != TOKEN:
        raise HTTPException(401, "bad token")


class SeedReq(BaseModel):
    template: str
    mode: str = "one_wrong"


class BrainReq(BaseModel):
    words: str
    patterns: str = "{a}{b}"
    suffixes: str = ""


class LoginReq(BaseModel):
    users: str
    passwords: str
    config: str


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html")) as f:
        return f.read()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/seed")
def start_seed(req: SeedReq, request: Request):
    auth(request)
    return worker.start(jobs.create("seed", req.model_dump())).snapshot()


@app.post("/api/brain")
def start_brain(req: BrainReq, request: Request):
    auth(request)
    return worker.start(jobs.create("brain", req.model_dump())).snapshot()


@app.post("/api/login")
def start_login(req: LoginReq, request: Request):
    auth(request)
    return worker.start(jobs.create("login", req.model_dump())).snapshot()


@app.get("/api/job/{jid}")
def get_job(jid: str, request: Request):
    auth(request)
    j = jobs.JOBS.get(jid)
    if not j:
        raise HTTPException(404, "no job")
    return j.snapshot()


@app.post("/api/job/{jid}/stop")
def stop_job(jid: str, request: Request):
    auth(request)
    j = jobs.JOBS.get(jid)
    if not j:
        raise HTTPException(404, "no job")
    worker.stop(j)
    return j.snapshot()


@app.get("/api/jobs")
def list_jobs(request: Request):
    auth(request)
    return [j.snapshot() for j in jobs.JOBS.values()]
