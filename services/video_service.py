import logging
import os
import uuid

import yt_dlp

from config import YOUTUBE_COOKIES_PATH, YT_DLP_JS_RUNTIMES

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

# Telegram bots can upload at most 50 MB per file. Stay a little under it so
# a slightly-off size estimate doesn't turn into a failed upload.
MAX_VIDEO_BYTES = 49 * 1024 * 1024

# The quality buttons offered (shorter side of the picture in pixels, so a
# vertical 1080x1920 Short counts as 1080p like a normal 1920x1080 video).
QUALITY_TIERS = (360, 720, 1080)


def _short_side(fmt):
    width, height = fmt.get("width"), fmt.get("height")
    if width and height:
        return min(width, height)
    return height or 0


def _has_video(fmt):
    return fmt.get("vcodec") not in (None, "none") and _short_side(fmt) > 0


def _has_audio(fmt):
    return fmt.get("acodec") not in (None, "none")


def _is_h264(fmt):
    codec = (fmt.get("vcodec") or "").lower()
    return codec.startswith("avc1") or codec.startswith("h264")


def _size(fmt):
    return fmt.get("filesize") or fmt.get("filesize_approx")


def _best_audio(formats):
    audio_only = [f for f in formats if _has_audio(f) and not _has_video(f)]
    if not audio_only:
        return None
    # m4a (AAC) merges into mp4 without re-encoding; then highest bitrate.
    return max(audio_only, key=lambda f: ((f.get("ext") == "m4a"), f.get("abr") or f.get("tbr") or 0))


def build_options(info):
    """
    Picks the video qualities to offer from a yt-dlp info dict. For each tier
    in QUALITY_TIERS it takes the best stream at or below that size (preferring
    H.264, which every Telegram app plays), drops duplicates, and drops
    qualities whose estimated size is over Telegram's upload limit.

    Returns a list (smallest first) of
    {"quality": 360, "selector": "<yt-dlp format string>", "bytes": estimate or None}.
    """

    formats = [f for f in (info.get("formats") or []) if f.get("format_id")]
    videos = [f for f in formats if _has_video(f)]
    if not videos:
        return []

    audio = _best_audio(formats)
    options = []
    seen = set()

    # Platforms like TikTok have no stream at or below 360: also offer their
    # smallest one, so there is always a lighter choice than the biggest.
    smallest = min(_short_side(f) for f in videos)
    tiers = QUALITY_TIERS if smallest <= QUALITY_TIERS[0] else (smallest,) + QUALITY_TIERS

    for tier in tiers:
        candidates = [f for f in videos if _short_side(f) <= tier]
        if not candidates:
            continue
        # Prefer a stream that carries its own audio only if no separate
        # audio exists to pair with (e.g. TikTok/Instagram single files);
        # otherwise the video-only stream pairs with the best audio.
        pick = max(
            candidates,
            key=lambda f: (_short_side(f), _is_h264(f), _has_audio(f), f.get("tbr") or 0),
        )
        quality = _short_side(pick)
        if quality in seen:
            continue

        if _has_audio(pick) or audio is None:
            selector = pick["format_id"]
            size = _size(pick)
        else:
            selector = f"{pick['format_id']}+{audio['format_id']}"
            video_size, audio_size = _size(pick), _size(audio)
            size = video_size + (audio_size or 0) if video_size else None

        if size and size > MAX_VIDEO_BYTES:
            continue

        seen.add(quality)
        options.append({"quality": quality, "selector": selector, "bytes": size})

    return options


def _base_options(url):
    options = {"quiet": True, "no_warnings": True, "noplaylist": True, "socket_timeout": 30}
    if "youtube.com" in url or "youtu.be" in url:
        if os.path.exists(YOUTUBE_COOKIES_PATH):
            options["cookiefile"] = YOUTUBE_COOKIES_PATH
        if YT_DLP_JS_RUNTIMES:
            options["js_runtimes"] = YT_DLP_JS_RUNTIMES
    return options


def _download(url, selector):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    options = _base_options(url)
    options.update({
        "format": selector,
        "merge_output_format": "mp4",
        # Random name: the title can hold characters that break paths, and two
        # people downloading the same video must never share a file.
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"video_{uuid.uuid4().hex}.%(ext)s"),
        "retries": 5,
        "fragment_retries": 5,
        "max_filesize": MAX_VIDEO_BYTES,
    })

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        # After merging, the real file is .mp4 whatever the source extension was.
        if not os.path.exists(path):
            merged = os.path.splitext(path)[0] + ".mp4"
            path = merged if os.path.exists(merged) else path

    return path, info


def download_video(url, option):
    """
    Downloads one video quality (an entry from build_options) and returns
    (file path, width, height, duration). Format ids can change between the
    moment the buttons were made and the tap, so if yt-dlp says the saved
    format is gone the options are rebuilt and the same quality is retried.
    """

    try:
        path, info = _download(url, option["selector"])
    except yt_dlp.utils.DownloadError as error:
        if "format" not in str(error).lower():
            raise
        logger.info("Saved video format is gone - looking it up again")
        with yt_dlp.YoutubeDL({**_base_options(url), "skip_download": True}) as ydl:
            fresh = build_options(ydl.extract_info(url, download=False))
        match = next((o for o in fresh if o["quality"] == option["quality"]), None)
        if not match:
            raise
        path, info = _download(url, match["selector"])

    if not os.path.exists(path):
        # yt-dlp skips (rather than fails) a download over max_filesize.
        raise ValueError("The file is too large to download.")

    if os.path.getsize(path) > MAX_VIDEO_BYTES:
        try:
            os.remove(path)
        except OSError:
            pass
        raise ValueError("The file is too large to download.")

    return path, info.get("width"), info.get("height"), info.get("duration")
