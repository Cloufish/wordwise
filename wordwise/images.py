"""Pexels image search/download for the Wordwise add-on."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from . import net

SEARCH_URL = "https://api.pexels.com/v1/search"


def search_and_download(word: str, api_key: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Search Pexels for `word` and download the first result's image bytes.

    Returns (image_bytes, error_reason). On success error_reason is None.
    On any failure image_bytes is None and error_reason describes why,
    so failures are no longer silent.
    """
    if not word:
        return None, "no word to search for"
    if not api_key:
        return None, "no Pexels API key configured"

    query = urllib.parse.urlencode({"query": word, "per_page": 1, "orientation": "landscape"})
    request = urllib.request.Request(
        f"{SEARCH_URL}?{query}",
        headers={"Authorization": api_key, "User-Agent": net.USER_AGENT},
    )
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

    try:
        image_request = urllib.request.Request(image_url, headers={"User-Agent": net.USER_AGENT})
        with net.open_url(image_request) as response:
            return response.read(), None
    except urllib.error.HTTPError as e:
        return None, f"image download HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"network error downloading image: {e.reason}"
    except Exception as e:
        return None, f"unexpected error downloading image: {e!r}"


def save_to_media(col, word: str, image_bytes: bytes) -> str:
    """Save image bytes into the collection's media folder, return the filename."""
    safe_word = "".join(c for c in word if c.isalnum()) or "wordwise"
    desired_name = f"wordwise_{safe_word}_{int(time.time() * 1000)}.jpg"
    return col.media.write_data(desired_name, image_bytes)
