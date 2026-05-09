import logging
import traceback
from datetime import datetime, timezone

from app.db import session_scope
from app.models import Link
from app.processors import generic, youtube

log = logging.getLogger("processors")

PROCESSORS = {
    "youtube": youtube.process,
    "web": generic.process,
    "x": generic.process,
    "instagram": generic.process,
}


def process_link(link_id: int) -> None:
    with session_scope() as s:
        link = s.get(Link, link_id)
        if link is None:
            log.warning("link %s not found", link_id)
            return
        link.status = "fetching"
        s.flush()
        url, site = link.url, link.site

    fn = PROCESSORS.get(site, generic.process)
    try:
        result = fn(url)
        with session_scope() as s:
            link = s.get(Link, link_id)
            if link is None:
                return
            link.title = result.get("title") or link.title
            link.description = result.get("description") or link.description
            link.metadata_json = result.get("metadata") or {}
            link.status = "done"
            link.error = None
            link.processed_at = datetime.now(timezone.utc)
        log.info("processed link %s (%s)", link_id, site)
    except Exception as exc:
        log.exception("failed to process link %s", link_id)
        with session_scope() as s:
            link = s.get(Link, link_id)
            if link is None:
                return
            link.status = "error"
            link.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}"
            link.processed_at = datetime.now(timezone.utc)
