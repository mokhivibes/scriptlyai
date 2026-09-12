import os
import yt_dlp


DOWNLOAD_DIR = "downloads"


def download_twitter_video(url: str):
    """
    Download only the audio track of an X/Twitter post's video and return
    (file path, post title).

    Unlike Instagram, X does expose separate audio-only streams for videos,
    so we can skip the video track here too, same as YouTube.
    """

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    output_template = os.path.join(
        DOWNLOAD_DIR,
        # Use the post's title so the file is recognizable later (falls back
        # to the post id if unavailable); the .100s cap keeps long post text
        # used as a title from producing unwieldy filenames.
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
