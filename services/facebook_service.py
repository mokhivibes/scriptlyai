import os
import yt_dlp


DOWNLOAD_DIR = "downloads"


def download_facebook_video(url: str):
    """
    Download a Facebook video (post, Watch, or fb.watch link) and return
    (file path, post title).

    Unlike YouTube/X, Facebook's own CDN doesn't reliably expose a
    separate audio-only stream - "bestaudio/best" still tries audio-only
    first (cheaper/faster when it exists) but falls back to the best
    combined video+audio format otherwise, same fallback shape as
    Instagram's downloader. extract_audio() (audio_service.py) pulls the
    audio track out afterward either way.
    """

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    output_template = os.path.join(
        DOWNLOAD_DIR,
        # Use the post's title so the file is recognizable later (falls
        # back to the post id if unavailable); the .100s cap keeps long
        # post text used as a title from producing unwieldy filenames.
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
