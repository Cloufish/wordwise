"""Image search/download for the Wordwise add-on: Pexels primary, Pixabay fallback."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from . import net

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/"

# Pixabay rejects per_page below 3, even though we only use the first result.
_PIXABAY_MIN_PER_PAGE = 3


class _RateLimiter:
    """Paces calls to at most one per `min_interval` seconds, across threads."""

    def __init__(self, min_interval: float):
        self._min_interval = min_interval
        self._lock = threading.Lock()
        self._last_at = 0.0

    def wait(self) -> None:
        with self._lock:
            remaining = self._last_at + self._min_interval - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            self._last_at = time.monotonic()


# Pexels' free tier is rate-limited to 200 requests/hour (per its docs). It's the
# primary/common-case provider, so this is the throttle that matters most.
_pexels_rate_limiter = _RateLimiter(3600 / 200)

# Pixabay allows up to 100 requests per 60 seconds per key; paced conservatively to
# ~1/second. It's only hit as a fallback when Pexels finds nothing, so this matters
# far less in practice. Only each provider's search endpoint is rate-limited (per
# their docs) — the CDN image download afterwards isn't, so it isn't throttled.
_pixabay_rate_limiter = _RateLimiter(1.0)


def _download(image_url: str) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        request = urllib.request.Request(image_url, headers={"User-Agent": net.USER_AGENT})
        with net.open_url(request) as response:
            return response.read(), None
    except urllib.error.HTTPError as e:
        return None, f"image download HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"network error downloading image: {e.reason}"
    except Exception as e:
        return None, f"unexpected error downloading image: {e!r}"


def _search_pexels(word: str, api_key: str) -> Tuple[Optional[bytes], Optional[str]]:
    if not api_key:
        return None, "no Pexels API key configured"

    query = urllib.parse.urlencode({"query": word, "per_page": 1, "orientation": "landscape"})
    request = urllib.request.Request(
        f"{PEXELS_SEARCH_URL}?{query}",
        headers={"Authorization": api_key, "User-Agent": net.USER_AGENT},
    )
    _pexels_rate_limiter.wait()
    try:
        with net.open_url(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return None, f"Pexels search HTTP {e.code}: {body or e.reason}"
    except urllib.error.URLError as e:
        return None, f"network error reaching Pexels: {e.reason}"
    except Exception as e:
        return None, f"unexpected error calling Pexels: {e!r}"

    photos = data.get("photos") or []
    if not photos:
        return None, "Pexels returned no results for this word"

    src = photos[0].get("src", {})
    image_url = src.get("medium") or src.get("small") or src.get("original")
    if not image_url:
        return None, "Pexels result had no usable image URL"

    return _download(image_url)


def _search_pixabay(word: str, api_key: str) -> Tuple[Optional[bytes], Optional[str]]:
    if not api_key:
        return None, "no Pixabay API key configured"

    query = urllib.parse.urlencode(
        {
            "key": api_key,
            "q": word,
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": _PIXABAY_MIN_PER_PAGE,
        }
    )
    request = urllib.request.Request(
        f"{PIXABAY_SEARCH_URL}?{query}",
        headers={"User-Agent": net.USER_AGENT},
    )
    _pixabay_rate_limiter.wait()
    try:
        with net.open_url(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return None, f"Pixabay search HTTP {e.code}: {body or e.reason}"
    except urllib.error.URLError as e:
        return None, f"network error reaching Pixabay: {e.reason}"
    except Exception as e:
        return None, f"unexpected error calling Pixabay: {e!r}"

    hits = data.get("hits") or []
    if not hits:
        return None, "Pixabay returned no results for this word"

    image_url = hits[0].get("webformatURL") or hits[0].get("largeImageURL")
    if not image_url:
        return None, "Pixabay result had no usable image URL"

    return _download(image_url)


def search_and_download(word: str, pexels_api_key: str, pixabay_api_key: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Search for an image of `word`: Pexels first, Pixabay as a fallback if Pexels
    finds nothing (missing key, no results, or a request error).

    Returns (image_bytes, error_reason). On success error_reason is None. On
    failure of both providers, image_bytes is None and error_reason describes
    why each one failed, so failures are never silent.

    Note: both providers' terms require downloading images before use rather
    than hotlinking their URLs — this function already does that (the caller
    embeds the returned bytes into the collection's media folder via
    save_to_media).
    """
    if not word:
        return None, "no word to search for"

    image_bytes, pexels_error = _search_pexels(word, pexels_api_key)
    if image_bytes:
        return image_bytes, None

    image_bytes, pixabay_error = _search_pixabay(word, pixabay_api_key)
    if image_bytes:
        return image_bytes, None

    return None, f"Pexels: {pexels_error}; Pixabay fallback: {pixabay_error}"


def save_to_media(col, word: str, image_bytes: bytes) -> str:
    """Save image bytes into the collection's media folder, return the filename."""
    safe_word = "".join(c for c in word if c.isalnum()) or "wordwise"
    desired_name = f"wordwise_{safe_word}_{int(time.time() * 1000)}.jpg"
    return col.media.write_data(desired_name, image_bytes)
