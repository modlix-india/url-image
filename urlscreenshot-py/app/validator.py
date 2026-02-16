import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class URL2ImageError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def validate_referrer(allowed_domains: set[str], referer: str | None) -> None:
    if not allowed_domains:
        return

    if referer is None:
        raise URL2ImageError("Referer header is missing", 403)

    try:
        parsed = urlparse(referer)
        host = parsed.hostname
    except Exception:
        logger.error("Unable to parse referer URL: %s", referer)
        raise URL2ImageError(f"Invalid referer URL: {referer}", 400)

    if not _domain_matches(host, allowed_domains):
        raise URL2ImageError(f"Referer domain is not allowed: {host}", 403)


def _domain_matches(host: str | None, allowed_domains: set[str]) -> bool:
    if host is None:
        return False
    for domain in allowed_domains:
        if domain.startswith("*."):
            # *.modlix.com matches foo.modlix.com, bar.baz.modlix.com
            if host.endswith(domain[1:]) or host == domain[2:]:
                return True
        elif host == domain:
            return True
    return False


def validate_and_get_url(request_path: str, key: str) -> str:
    """Extract and validate URL from request path.

    Replicates Java URL2ImageValidator.validateAndGetURL():
    1. Find key ("url2image") in path, take everything after
    2. Replace "//" with "/"
    3. Strip leading "/"
    4. "https/" → "https://", "http/" → "http://", else prepend "https://"
    """
    url = request_path.strip()

    if not url:
        logger.error("URL is missing")
        raise URL2ImageError("URL is missing", 400)

    if key:
        index = url.find(key)
        if index == -1:
            logger.error("Key is missing in URL: %s", key)
            raise URL2ImageError(f"Key is missing in URL: {key}", 400)
        url = url[index + len(key) :].strip()

    url = url.replace("//", "/")

    if url.startswith("/"):
        url = url[1:]

    if url.startswith("https/"):
        url = "https://" + url[6:]
    elif url.startswith("http/"):
        url = "http://" + url[5:]
    else:
        url = "https://" + url

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Missing scheme or netloc")
    except Exception:
        logger.error("Invalid URL: %s", url)
        raise URL2ImageError(f"Invalid URL: {url}", 400)

    return url
