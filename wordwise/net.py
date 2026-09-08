"""Shared HTTP helpers for Wordwise's outbound lookups (Pixabay, Wiktionary)."""

from __future__ import annotations

import ssl
import urllib.request

# Python's default urllib User-Agent ("Python-urllib/x.y") is commonly blocked by
# Cloudflare's WAF (a problem observed with the previous image provider, Pexels,
# which returned a 403 "error code 1010" for it) before the request ever reaches
# the API. It's also discouraged by Wikimedia's API etiquette policy for the
# Wiktionary API. A normal, identifying UA avoids both.
USER_AGENT = "Mozilla/5.0 (compatible; Wordwise-Anki-Addon/0.1)"

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = None


def open_url(request_or_url, timeout: int = 15):
    return urllib.request.urlopen(request_or_url, timeout=timeout, context=_SSL_CONTEXT)
