"""Offline word-frequency lookups against Hermit Dave FrequencyWords lists.

Each list file is plain text, one "word count" pair per line
(see https://github.com/hermitdave/FrequencyWords), e.g.:

    the 23135851162
    be  12545825841
"""

from __future__ import annotations

import os
from typing import Optional

# path -> (mtime, {word: count_str})
_cache: dict = {}


def load_list(path: str) -> dict:
    mtime = os.path.getmtime(path)
    cached = _cache.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    words: dict = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            word, count = parts[0], parts[1]
            words[word.lower()] = count

    _cache[path] = (mtime, words)
    return words


def lookup(word: str, path: str) -> Optional[str]:
    if not word or not path:
        return None
    try:
        words = load_list(path)
    except OSError:
        return None
    return words.get(word.strip().lower())
