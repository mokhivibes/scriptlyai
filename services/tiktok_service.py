import os
import yt_dlp


DOWNLOAD_DIR = "downloads"


def download_tiktok_video(url: str):
    """
    Download only the audio track of a TikTok video and return
    (file path, video title/caption).

    NOTE: unlike YouTube/Instagram/X, this has never been exercised
    against a real TikTok URL - TikTok is blocked at the ISP/network level
    from the development machine (see memory: tiktok-network-block), so
    this mirrors the working X/Twitter pattern but is unverified. The
    format selector falls back to "best" (full muxed video+audio) if no
    separate audio-only stream is available, same safety net as Instagram.
    """

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    output_template = os.path.join(
        DOWNLOAD_DIR,
        # Use the video's title/caption so the file is recognizable later
        # (falls back to the video id if unavailable); the .100s cap keeps
        # long TikTok captions from producing unwieldy filenames.
        "%(title,id).100s.%(ext)s"
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # See youtube_service.py's identical option - yt-dlp's Python API
        # does not apply its CLI default of 10 retries unless set explicitly.
        "retries": 5,
        "fragment_retries": 5,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)
        title = info.get("title")

        return filename, title
