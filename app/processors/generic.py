import httpx
from selectolax.parser import HTMLParser

UA = "Mozilla/5.0 (linkstash) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "en;q=0.9"}


def _meta(tree: HTMLParser, *names: str) -> str | None:
    for name in names:
        el = tree.css_first(f'meta[property="{name}"]') or tree.css_first(f'meta[name="{name}"]')
        if el and (content := el.attributes.get("content")):
            return content.strip()
    return None


def process(url: str) -> dict:
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=20.0) as client:
        resp = client.get(url)
    final_url = str(resp.url)

    metadata: dict = {
        "final_url": final_url,
        "status_code": resp.status_code,
        "content_type": resp.headers.get("content-type"),
    }
    if resp.status_code >= 400:
        return {"title": None, "description": None, "metadata": metadata}

    ctype = (resp.headers.get("content-type") or "").lower()
    if "html" not in ctype:
        return {"title": None, "description": None, "metadata": metadata}

    tree = HTMLParser(resp.text)
    title = _meta(tree, "og:title", "twitter:title")
    if not title:
        t = tree.css_first("title")
        title = t.text(strip=True) if t else None
    description = _meta(tree, "og:description", "twitter:description", "description")
    image = _meta(tree, "og:image", "twitter:image")
    site_name = _meta(tree, "og:site_name")

    if image:
        metadata["image"] = image
    if site_name:
        metadata["site_name"] = site_name

    return {
        "title": title,
        "description": description,
        "metadata": metadata,
    }
