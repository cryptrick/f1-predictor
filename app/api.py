from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.config import settings
from app.db import init_db, session_scope
from app.models import Link
from app.services import ingest

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, title="linkstash")


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str | None = Query(default=None),
    site: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    with session_scope() as s:
        stmt = select(Link).order_by(Link.received_at.desc()).limit(200)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Link.title.ilike(like), Link.url.ilike(like), Link.note.ilike(like)))
        if site:
            stmt = stmt.where(Link.site == site)
        if status:
            stmt = stmt.where(Link.status == status)
        links = list(s.scalars(stmt).all())
        sites = [r[0] for r in s.execute(select(Link.site).distinct()).all()]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "links": links, "q": q, "site": site, "status": status, "sites": sites},
    )


@app.get("/links/{link_id}", response_class=HTMLResponse)
def link_detail(request: Request, link_id: int):
    with session_scope() as s:
        link = s.get(Link, link_id)
        if link is None:
            raise HTTPException(404)
    return templates.TemplateResponse("link.html", {"request": request, "link": link})


@app.get("/links/{link_id}.json")
def link_json(link_id: int):
    with session_scope() as s:
        link = s.get(Link, link_id)
        if link is None:
            raise HTTPException(404)
        return JSONResponse(
            {
                "id": link.id,
                "url": link.url,
                "source": link.source,
                "site": link.site,
                "status": link.status,
                "title": link.title,
                "description": link.description,
                "note": link.note,
                "metadata": link.metadata_json,
                "ingest_payload": link.ingest_payload,
                "error": link.error,
                "received_at": link.received_at.isoformat() if link.received_at else None,
                "processed_at": link.processed_at.isoformat() if link.processed_at else None,
            }
        )


class IngestRequest(BaseModel):
    url: str
    note: str | None = None


@app.post("/ingest")
def ingest_endpoint(req: IngestRequest, authorization: str | None = Header(default=None)):
    tokens = settings.ingest_token_set
    if not tokens:
        raise HTTPException(404)
    expected = f"Bearer "
    if not authorization or not authorization.startswith(expected):
        raise HTTPException(401)
    if authorization[len(expected) :].strip() not in tokens:
        raise HTTPException(401)
    link_id = ingest(req.url, source="api", note=req.note)
    return {"id": link_id}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/favicon.ico")
def favicon():
    return RedirectResponse("/", status_code=302)
