import asyncio
import base64
import os
from typing import Optional, Tuple

import yt_dlp

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(DOWNLOAD_DIR, "cookies.txt")


def _write_cookies() -> Optional[str]:
    """Optional: YT_COOKIES_B64 env (base64 of a Netscape cookies.txt)."""
    raw = os.getenv("YT_COOKIES_B64", "").strip()
    if not raw:
        return None
    try:
        with open(COOKIES_FILE, "wb") as fh:
            fh.write(base64.b64decode(raw))
        return COOKIES_FILE
    except Exception:  # noqa: BLE001
        return None


_COOKIES = _write_cookies()


def _opts(download: bool) -> dict:
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "retries": 3,
        "socket_timeout": 30,
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(extractor)s-%(id)s.%(ext)s"),
        "extractor_args": {
            "youtube": {"player_client": ["android_vr", "web_safari", "web"]}
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    }
    if _COOKIES:
        opts["cookiefile"] = _COOKIES
    if download:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ]
    else:
        opts["skip_download"] = True
    return opts


def _pick(info: dict) -> dict:
    if info.get("entries"):
        entries = [e for e in info["entries"] if e]
        if not entries:
            raise ValueError("no results")
        info = entries[0]
    return {
        "id": info.get("id"),
        "extractor": info.get("extractor_key", info.get("extractor", "")).lower(),
        "title": info.get("title", "Unknown"),
        "duration": int(info.get("duration") or 0),
        "url": info.get("webpage_url") or info.get("original_url") or "",
        "thumb": info.get("thumbnail"),
    }


def _resolve_sync(query: str) -> Tuple[dict, str]:
    is_link = query.startswith("http://") or query.startswith("https://")
    targets = [query] if is_link else [f"ytsearch1:{query}", f"scsearch1:{query}"]

    last_error: Optional[Exception] = None
    for target in targets:
        try:
            with yt_dlp.YoutubeDL(_opts(download=False)) as ydl:
                meta = _pick(ydl.extract_info(target, download=False))
            with yt_dlp.YoutubeDL(_opts(download=True)) as ydl:
                info = ydl.extract_info(meta["url"] or target, download=True)
            if info.get("entries"):
                info = [e for e in info["entries"] if e][0]
            path = os.path.join(
                DOWNLOAD_DIR,
                f"{info.get('extractor', '')}-{info['id']}.mp3",
            )
            if not os.path.exists(path):
                # fall back to whatever the postprocessor produced
                for name in os.listdir(DOWNLOAD_DIR):
                    if info["id"] in name and name.endswith(".mp3"):
                        path = os.path.join(DOWNLOAD_DIR, name)
                        break
            if not os.path.exists(path):
                raise FileNotFoundError("audio file missing after download")
            return meta, path
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    raise last_error or ValueError("nothing found")


async def resolve(query: str) -> Optional[Tuple[dict, str]]:
    return await asyncio.to_thread(_resolve_sync, query)


def format_duration(seconds: int) -> str:
    seconds = int(seconds or 0)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
