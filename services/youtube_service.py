import os
import yt_dlp


DOWNLOAD_DIR = "downloads"


def download_youtube_video(url: str):
    """
    Download only the audio track of a YouTube video and return
    (file path, video title).

    We never need the video stream (only the transcript), so skipping it
    avoids Telegram's "file too large" errors and makes downloads much
    faster.
    """

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    output_template = os.path.join(
        DOWNLOAD_DIR,
        # Use the video's title so the file is recognizable later (falls
        # back to the video id if a title isn't available). yt-dlp
        # sanitizes unsafe filename characters automatically; the .100s
        # length cap keeps very long titles from producing unwieldy filenames.
        "%(title,id).100s.%(ext)s"
    )

    options = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # yt-dlp's Python API does NOT pick up its own CLI default of 10
        # retries when this key is left unset - params.get('retries')
        # returns None, and yt-dlp's RetryManager treats that as `0` (no
        # retries at all). Set explicitly so transient network hiccups
        # during download get retried instead of failing on the first blip.
        "retries": 5,
        "fragment_retries": 5,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)
        title = info.get("title")

        return filename, title