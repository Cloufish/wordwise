"""Noun-gender lookup via freedictionaryapi.com (a structured, Wiktionary-backed
dictionary API — no API key required).

Unlike scraping each Wiktionary language edition's own wikitext conventions
(which vary wildly and required a bespoke, hand-verified parser per language),
this API returns a uniform JSON shape for every language it covers:

    { "entries": [ { "partOfSpeech": "noun", "senses": [ {"tags": [...]}, ... ] } ] }

Gender shows up as one of the literal strings "masculine" / "feminine" / "neuter"
inside a sense's "tags" array (verified live for German, French, and others while
building this). Only the noun entry's own senses are scanned — not "forms" (which
lists derived/related words like diminutives that can have a different gender).

The language is a free-text ISO 639-1/639-3 code (e.g. "de", "fr", "ja"), since
this single implementation works the same way regardless of language — including
languages that don't have grammatical gender at all, which will just consistently
report "no gender tag found" rather than anything misleading.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Optional, Tuple

from . import net

API_BASE = "https://freedictionaryapi.com/api/v1/entries"

_GENDER_TAGS = ("masculine", "feminine", "neuter")

DEFAULT_LANGUAGE = "de"


def lookup(word: str, language_code: str) -> Tuple[Optional[str], Optional[str]]:
    """Look up the grammatical gender of `word` in the given language.

    Returns (gender_value, error_reason). On success error_reason is None.
    On any failure gender_value is None and error_reason describes why.
    """
    if not word:
        return None, "no word to search for"

    language_code = (language_code or "").strip()
    if not language_code:
        return None, "no gender language configured"

    url = f"{API_BASE}/{urllib.parse.quote(language_code)}/{urllib.parse.quote(word)}"
    request = urllib.request.Request(url, headers={"User-Agent": net.USER_AGENT})

    try:
        with net.open_url(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"freedictionaryapi.com HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"network error reaching freedictionaryapi.com: {e.reason}"
    except Exception as e:
        return None, f"unexpected error calling freedictionaryapi.com: {e!r}"

    entries = data.get("entries") or []
    if not entries:
        return None, f"no dictionary entry found for '{word}' ({language_code})"

    noun_entry = next((e for e in entries if e.get("partOfSpeech") == "noun"), None)
    if noun_entry is None:
        return None, f"'{word}' has a dictionary entry but isn't tagged as a noun ({language_code})"

    values: List[str] = []
    for sense in noun_entry.get("senses") or []:
        for tag in sense.get("tags") or []:
            if tag in _GENDER_TAGS and tag not in values:
                values.append(tag)

    if not values:
        return None, f"found a noun entry for '{word}' but no gender tag was present ({language_code})"

    return "/".join(values), None
