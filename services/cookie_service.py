import logging
import os
import shutil
import time

import yt_dlp

from config import YOUTUBE_COOKIES_PATH, YT_DLP_JS_RUNTIMES

logger = logging.getLogger(__name__)

# Cookies that actually prove a Google login - a file without any of them
# cannot unlock YouTube however many other cookies it holds.
_LOGIN_COOKIES = ("__Secure-3PSID", "__Secure-1PSID", "SID", "LOGIN_INFO", "__Secure-3PAPISID", "SAPISID")

# A short public video used to check that YouTube accepts the cookies.
_CHECK_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

MAX_COOKIE_FILE_BYTES = 2 * 1024 * 1024


def parse_cookie_file(text: str):
    """
    Reads a Netscape-format cookies.txt (what the "Get cookies.txt" browser
    extension exports). Returns (info, problem): info is
    {"cookies": count, "login_expires": epoch or None (None = session cookie /
    unknown)}, problem is a plain-English reason when it is not usable.
    """

    total = 0
    login_expiries = []
    saw_login_cookie = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        elif line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 7:
            continue
        domain, _flag, _path, _secure, expiry, name, _value = fields
        if "youtube.com" not in domain and "google.com" not in domain:
            continue
        total += 1
        if name in _LOGIN_COOKIES:
            saw_login_cookie = True
            try:
                if int(expiry) > 0:
                    login_expiries.append(int(expiry))
            except ValueError:
                pass

    if total == 0:
        return None, "That doesn't look like a cookies.txt file for youtube.com."
    if not saw_login_cookie:
        return None, "The file has no Google sign-in cookies - it was exported while signed out."

    return {"cookies": total, "login_expires": min(login_expiries) if login_expiries else None}, None


def cookie_status(path: str = None):
    """(days_left or None, problem) for the installed cookie file."""

    path = path or YOUTUBE_COOKIES_PATH
    if not os.path.exists(path):
        return None, "no cookie file installed"
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            info, problem = parse_cookie_file(file.read())
    except OSError as error:
        return None, f"could not read it ({error})"
    if problem:
        return None, problem
    if info["login_expires"] is None:
        return None, None
    return (info["login_expires"] - time.time()) / 86400, None


def verify_with_youtube(path: str) -> bool:
    """True if YouTube serves a video with these cookies."""

    options = {"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 30, "cookiefile": path}
    if YT_DLP_JS_RUNTIMES:
        options["js_runtimes"] = YT_DLP_JS_RUNTIMES
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(_CHECK_VIDEO, download=False)
        return bool(info and info.get("formats"))
    except Exception as error:
        logger.warning(f"YouTube rejected the new cookies: {str(error)[:150]}")
        return False


def install_cookies(text: str):
    """
    Validates, tests and installs a new cookie file. Returns (ok, message).
    The old file is kept as <name>.bak and restored if anything goes wrong.
    """

    info, problem = parse_cookie_file(text)
    if problem:
        return False, problem

    candidate = YOUTUBE_COOKIES_PATH + ".new"
    with open(candidate, "w", encoding="utf-8") as file:
        file.write(text)
    os.chmod(candidate, 0o600)

    if not verify_with_youtube(candidate):
        os.remove(candidate)
        return False, "YouTube did not accept these cookies (signed out, or the account is blocked). The old file is still in use."

    if os.path.exists(YOUTUBE_COOKIES_PATH):
        shutil.copy2(YOUTUBE_COOKIES_PATH, YOUTUBE_COOKIES_PATH + ".bak")
    os.replace(candidate, YOUTUBE_COOKIES_PATH)

    if info["login_expires"]:
        days = int((info["login_expires"] - time.time()) / 86400)
        when = f"The sign-in lasts about {days} more days."
    else:
        when = "The sign-in is a session cookie, so it may stop sooner - check /stats in a few days."
    return True, f"{info['cookies']} cookies installed and YouTube accepted them. {when}"
