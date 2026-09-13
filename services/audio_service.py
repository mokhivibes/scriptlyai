import os
import shutil
import subprocess

# A bare "ffmpeg"/"ffprobe" resolves fine when this script is run manually
# (inherits the interactive shell's full PATH), but fails with
# FileNotFoundError under launchd - launchd's default job environment PATH
# is minimal (typically just /usr/bin:/bin:/usr/sbin:/sbin) and doesn't
# include Homebrew's install location. shutil.which() checks the process's
# actual current PATH first (so this keeps working if that's ever fixed or
# extended), then falls back to Homebrew's two possible prefixes (Apple
# Silicon vs Intel) - more robust than hardcoding one absolute path, since
# it keeps working regardless of how the process is launched (launchd,
# manually, a different process manager later) or which Mac architecture
# it runs on, without depending on any one deployment's environment
# configuration staying correct.
_COMMON_INSTALL_DIRS = ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin")


def _resolve_binary(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found

    for directory in _COMMON_INSTALL_DIRS:
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    raise FileNotFoundError(
        f"Could not find '{name}' on PATH or in any common install location "
        f"({', '.join(_COMMON_INSTALL_DIRS)}). Is ffmpeg installed?"
    )


# Resolved once at import time, not per-call - if ffmpeg genuinely isn't
# installed, this fails loudly at bot startup (visible immediately in
# logs) rather than deep inside a user's request with a cryptic error.
FFPROBE_PATH = _resolve_binary("ffprobe")
FFMPEG_PATH = _resolve_binary("ffmpeg")


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
        [FFPROBE_PATH, "-i", video_path, "-show_streams", "-select_streams", "a",
         "-loglevel", "error"],
        capture_output=True,
        text=True,
    )
    if not probe.stdout.strip():
        raise ValueError("This video does not contain an audio track.")

    audio_path = os.path.splitext(video_path)[0] + ".mp3"

    command = [
        FFMPEG_PATH,
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