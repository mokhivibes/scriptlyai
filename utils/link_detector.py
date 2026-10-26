import re
from urllib.parse import parse_qs, urlparse

# Platform -> registered domains. A host matches if it IS the domain or a
# subdomain of it (m.youtube.com, music.youtube.com, vt.tiktok.com,
# web.facebook.com, mobile.twitter.com ...). Matching on the parsed hostname,
# never a substring, keeps look-alikes (youtube.com.evil.com, evil.com/?u=
# youtube.com, youtube.com@evil.com) from being treated as a supported
# platform - links are handed to yt-dlp, so a lenient match would let someone
# make the server fetch arbitrary URLs.
_PLATFORM_DOMAINS = {
    "youtube": ("youtube.com", "youtu.be"),
    "instagram": ("instagram.com", "instagr.am"),
    "tiktok": ("tiktok.com",),
    "facebook": ("facebook.com", "fb.watch", "fb.com"),
    "twitter": ("twitter.com", "x.com"),
}


def detect_platform(url: str):
    """
    Detect the social media platform from a URL.

    Returns "youtube", "instagram", "tiktok", "facebook", "twitter", or None
    (also None for anything that isn't a plain http/https link).
    """

    try:
        parsed_url = urlparse(url)

        if parsed_url.scheme not in ("http", "https"):
            return None

        host = (parsed_url.hostname or "").lower().rstrip(".")
        if not host:
            return None

        for platform, domains in _PLATFORM_DOMAINS.items():
            for domain in domains:
                if host == domain or host.endswith("." + domain):
                    return platform

        return None

    except Exception:
        return None


# Characters that end a sentence or close a bracket right after a pasted
# link ("see https://youtu.be/abc).") but are never part of one of these URLs.
_TRAILING_PUNCTUATION = ".,;:!?)]}>'\"\u00bb\u201d\u2019"


# A link pasted without "https://" (youtu.be/abc, www.instagram.com/reel/x).
# Only the supported platforms' own domains qualify, so ordinary text such as
# "version 2.0" or "notes.txt" is never mistaken for a link.
_BARE_LINK_PATTERN = re.compile(
    r"(?<![\w@/.-])((?:[a-z0-9-]+\.)*"
    r"(?:youtube\.com|youtu\.be|instagram\.com|instagr\.am|tiktok\.com|facebook\.com|fb\.watch|fb\.com|twitter\.com|x\.com)"
    r"/[^\s]+)",
    re.IGNORECASE,
)


def extract_url(text: str):
    """
    Find the first URL inside a message (adding https:// to a bare
    supported-platform link).
    """

    url_pattern = r"https?://[^\s]+"

    match = re.search(url_pattern, text)

    if match:
        return match.group(0).rstrip(_TRAILING_PUNCTUATION)

    bare = _BARE_LINK_PATTERN.search(text)

    if bare:
        return "https://" + bare.group(1).rstrip(_TRAILING_PUNCTUATION)

    return None


def canonical_link_key(url: str, platform: str):
    """
    A stable identity for the VIDEO a link points to - the same video behind
    youtu.be/x, youtube.com/watch?v=x and /shorts/x (with or without tracking
    parameters) gets the same key, so a repeat request can be served from
    memory. Returns None when the video can't be identified from the URL
    alone (e.g. an unresolved short link) - those simply aren't cached.
    """

    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = [part for part in parsed.path.split("/") if part]
        query = parse_qs(parsed.query)

        if platform == "youtube":
            if host.endswith("youtu.be") and path:
                video_id = path[0]
            elif "v" in query:
                video_id = query["v"][0]
            elif len(path) >= 2 and path[0] in ("shorts", "embed", "live", "v"):
                video_id = path[1]
            else:
                return None
            return f"youtube:{video_id}" if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id) else None

        if platform == "instagram":
            for index, part in enumerate(path[:-1]):
                if part in ("reel", "reels", "p", "tv"):
                    return f"instagram:{path[index + 1]}"
            return None

        if platform == "tiktok":
            if "video" in path and path.index("video") + 1 < len(path):
                return f"tiktok:{path[path.index('video') + 1]}"
            if host.split(".")[0] in ("vm", "vt") and path:
                return f"tiktok-short:{path[0]}"
            return None

        if platform == "facebook":
            if "v" in query:
                return f"facebook:{query['v'][0]}"
            if host.endswith("fb.watch") and path:
                return f"facebook-short:{path[0]}"
            for index, part in enumerate(path[:-1]):
                if part in ("videos", "reel", "reels"):
                    return f"facebook:{path[index + 1]}"
            return None

        if platform == "twitter":
            if "status" in path and path.index("status") + 1 < len(path):
                status_id = path[path.index("status") + 1]
                return f"twitter:{status_id}" if status_id.isdigit() else None
            return None

        return None
    except Exception:
        return None
