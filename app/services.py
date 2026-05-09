from urllib.parse import urlparse

from app.db import session_scope
from app.models import Link
from app.queue import default_queue


def detect_site(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host in {"youtube.com", "m.youtube.com", "youtu.be"} or host.endswith(".youtube.com"):
        return "youtube"
    if host in {"x.com", "twitter.com"} or host.endswith(".twitter.com"):
        return "x"
    if host == "instagram.com" or host.endswith(".instagram.com"):
        return "instagram"
    return "web"


def ingest(url: str, source: str, payload: dict | None = None, note: str | None = None) -> int:
    site = detect_site(url)
    with session_scope() as s:
        link = Link(url=url, source=source, site=site, ingest_payload=payload, note=note)
        s.add(link)
        s.flush()
        link_id = link.id
    default_queue.enqueue("app.processors.router.process_link", link_id, job_timeout=300)
    return link_id
