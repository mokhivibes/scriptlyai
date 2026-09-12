import re
from urllib.parse import urlparse


def detect_platform(url: str):
    """
    Detect the social media platform from a URL.

    Returns:
        "youtube"
        "instagram"
        "tiktok"
        "facebook"
        "twitter"
        None
    """

    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]

        if domain in ("youtube.com", "youtu.be"):
            return "youtube"

        if domain in ("instagram.com", "instagr.am"):
            return "instagram"

        if domain in ("tiktok.com", "vm.tiktok.com"):
            return "tiktok"

        if domain in ("facebook.com", "fb.watch"):
            return "facebook"

        if domain in ("twitter.com", "x.com"):
            return "twitter"

        return None

    except Exception:
        return None


def extract_url(text: str):
    """
    Find the first URL inside a message.
    """

    url_pattern = r"https?://[^\s]+"

    match = re.search(url_pattern, text)

    if match:
        return match.group(0)

    return None