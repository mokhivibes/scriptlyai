import re
from urllib.parse import urlparse

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


def extract_url(text: str):
    """
    Find the first URL inside a message.
    """

    url_pattern = r"https?://[^\s]+"

    match = re.search(url_pattern, text)

    if match:
        return match.group(0).rstrip(_TRAILING_PUNCTUATION)

    return None
