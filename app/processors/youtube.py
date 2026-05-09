from yt_dlp import YoutubeDL

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
    "extract_flat": False,
}


def process(url: str) -> dict:
    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
    metadata = {
        "id": info.get("id"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "upload_date": info.get("upload_date"),
        "thumbnail": info.get("thumbnail"),
        "tags": info.get("tags"),
        "categories": info.get("categories"),
        "webpage_url": info.get("webpage_url"),
    }
    return {
        "title": info.get("title"),
        "description": (info.get("description") or "")[:4000] or None,
        "metadata": {k: v for k, v in metadata.items() if v is not None},
    }
