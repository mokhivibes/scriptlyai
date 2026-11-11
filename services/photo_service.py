import logging
import os
import re
import subprocess
import uuid

import requests
import yt_dlp

from config import MAX_DOWNLOAD_BYTES
from services.audio_service import FFMPEG_PATH

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

# Telegram shows an album of at most 10; a post with more is sent as several albums.
MAX_PHOTOS = 30

# Telegram refuses photos over 10 MB.
MAX_PHOTO_BYTES = 10 * 1024 * 1024

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tiktok.com/",
}


def _from_instagram(url):
    """
    Instagram photo posts: yt-dlp finds them but refuses ("no video in this
    post"), keeping the picture links as thumbnails. A carousel comes back as
    a playlist - its picture entries are used, its video entries skipped.
    """

    options = {"quiet": True, "no_warnings": True, "skip_download": True,
               "ignore_no_formats_error": True, "socket_timeout": 20}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = list(info.get("entries") or [info])
    images = []
    for entry in entries:
        if entry and not entry.get("formats"):
            best = _largest_image([t["url"] for t in (entry.get("thumbnails") or []) if t.get("url")])
            if best:
                images.append(best)

    return {"images": images, "audio_url": None, "title": info.get("title")} if images else None


def _largest_image(urls):
    """Instagram lists the same picture at several sizes without saying which
    is which - the biggest file is the full-size one."""

    best, best_size = None, -1
    for candidate in urls[:6]:
        try:
            response = requests.head(candidate, headers=_BROWSER_HEADERS, timeout=10, allow_redirects=True)
            size = int(response.headers.get("Content-Length") or 0)
        except Exception:
            continue
        if size > best_size:
            best, best_size = candidate, size
    return best or (urls[0] if urls else None)


def _resolve_tiktok(url):
    """tiktok.com/t/CODE and vm.tiktok.com links redirect to the real post URL."""

    if re.search(r"/(?:video|photo)/\d+", url):
        return url
    try:
        from curl_cffi import requests as curl_requests
        return curl_requests.get(url, impersonate="chrome", timeout=20, allow_redirects=True).url
    except Exception:
        return requests.get(url, headers=_BROWSER_HEADERS, timeout=20, allow_redirects=True).url


def _from_tiktok(url):
    """
    TikTok photo posts ("photo mode" slideshows): yt-dlp has no support for
    them, but its page reader can fetch the post data, which lists the
    pictures and the music. Uses a private yt-dlp method, so any failure just
    means "not a photo post" and the normal error path takes over.
    """

    final_url = _resolve_tiktok(url)
    match = re.search(r"/(?:video|photo)/(\d+)", final_url)
    if not match:
        return None
    post_id = match.group(1)

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "socket_timeout": 20}) as ydl:
        extractor = ydl.get_info_extractor("TikTok")
        data, _status = extractor._extract_web_data_and_status(final_url, post_id)

    image_post = data.get("imagePost") or {}
    images = []
    for image in image_post.get("images") or []:
        urls = (image.get("imageURL") or {}).get("urlList") or []
        if urls:
            images.append(urls[0])

    if not images:
        return None

    music = data.get("music") or {}
    return {"images": images, "audio_url": music.get("playUrl") or None, "title": data.get("desc") or music.get("title")}


def find_photos(url, platform):
    """
    The pictures (and music, if any) of a photo post, as
    {"images": [url, ...], "audio_url": url or None, "title": str or None},
    or None when this link isn't a photo post / can't be read.
    """

    try:
        if platform == "instagram":
            result = _from_instagram(url)
        elif platform == "tiktok":
            result = _from_tiktok(url)
        else:
            return None
    except Exception as error:
        logger.info(f"No photos found for this link ({type(error).__name__}: {str(error)[:120]})")
        return None

    if result:
        result["images"] = result["images"][:MAX_PHOTOS]
    return result


def _fetch(url, path):
    with requests.get(url, headers=_BROWSER_HEADERS, timeout=30, stream=True) as response:
        response.raise_for_status()
        written = 0
        with open(path, "wb") as file:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                written += len(chunk)
                if written > MAX_DOWNLOAD_BYTES:
                    raise ValueError("The file is too large to download.")
                file.write(chunk)


def download_photos(image_urls):
    """
    Downloads the pictures and makes sure each is a JPEG Telegram will accept
    (TikTok serves webp/heic). Returns the file paths; pictures that fail are
    skipped.
    """

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    paths = []
    for url in image_urls:
        raw = os.path.join(DOWNLOAD_DIR, f"photo_{uuid.uuid4().hex}.img")
        jpg = raw[:-4] + ".jpg"
        try:
            _fetch(url, raw)
            subprocess.run(
                [FFMPEG_PATH, "-loglevel", "error", "-i", raw, "-frames:v", "1", "-q:v", "2", "-y", jpg],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
            )
            if os.path.getsize(jpg) > MAX_PHOTO_BYTES:
                os.remove(jpg)
                continue
            paths.append(jpg)
        except Exception as error:
            logger.warning(f"Skipping one picture ({type(error).__name__})")
        finally:
            if os.path.exists(raw):
                os.remove(raw)
    return paths


def download_audio(audio_url):
    """The post's music as a file Telegram can send as audio, or None."""

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    raw = os.path.join(DOWNLOAD_DIR, f"photoaudio_{uuid.uuid4().hex}.src")
    mp3 = raw[:-4] + ".mp3"
    try:
        _fetch(audio_url, raw)
        subprocess.run(
            [FFMPEG_PATH, "-loglevel", "error", "-i", raw, "-vn", "-acodec", "mp3", "-y", mp3],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120,
        )
        return mp3
    except Exception as error:
        logger.warning(f"Could not get the post's audio ({type(error).__name__})")
        return None
    finally:
        if os.path.exists(raw):
            os.remove(raw)
