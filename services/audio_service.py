import os
import subprocess


def extract_audio(video_path: str):
    """
    Extract audio from a video file and save it as MP3.

    Returns:
        Path to the MP3 audio file.
    """

    # Some posts (e.g. GIFs posted as "video" on X/Twitter) have no audio
    # track at all - check first so we can raise a clear error instead of
    # ffmpeg failing with a generic non-zero exit code.
    probe = subprocess.run(
        ["ffprobe", "-i", video_path, "-show_streams", "-select_streams", "a",
         "-loglevel", "error"],
        capture_output=True,
        text=True,
    )
    if not probe.stdout.strip():
        raise ValueError("This video does not contain an audio track.")

    audio_path = os.path.splitext(video_path)[0] + ".mp3"

    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "mp3",
        "-y",
        audio_path,
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return audio_path