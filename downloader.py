import asyncio
import os
from typing import Optional, Tuple

import yt_dlp

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
}


def _search_sync(query: str) -> Optional[dict]:
    opts = dict(_YDL_OPTS)
    opts["skip_download"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        if query.startswith("http://") or query.startswith("https://"):
            info = ydl.extract_info(query, download=False)
        else:
            res = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = (res or {}).get("entries") or []
            if not entries:
                return None
            info = entries[0]
    return {
        "id": info.get("id"),
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration") or 0,
        "url": info.get("webpage_url") or query,
        "thumb": info.get("thumbnail"),
    }


def _download_sync(url: str) -> str:
    with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=True)
    return os.path.join(DOWNLOAD_DIR, f"{info['id']}.mp3")


async def search(query: str) -> Optional[dict]:
    return await asyncio.to_thread(_search_sync, query)


async def download(url: str) -> str:
    return await asyncio.to_thread(_download_sync, url)


async def resolve(query: str) -> Optional[Tuple[dict, str]]:
    info = await search(query)
    if not info:
        return None
    path = await download(info["url"])
    return info, path


def format_duration(seconds: int) -> str:
    seconds = int(seconds or 0)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
