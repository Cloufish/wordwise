"""Noun-gender lookup via Wiktionary, for a small set of verified languages.

Each Wiktionary language edition marks a noun's grammatical gender with its own,
incompatible convention (verified live against the real APIs while building this):

- German (de.wiktionary.org):  {{Deutsch Substantiv Übersicht|Genus=m|...}}
- French (fr.wiktionary.org):  standalone {{m}} / {{f}} near the headword, under
                                the {{S|nom|fr}} part-of-speech heading
- Spanish (es.wiktionary.org): gender is *in the template name* itself, e.g.
                                {{sustantivo masculino|es}}
- Portuguese (pt.wiktionary.org): {{gramática|m}}

Other large editions (Russian, Italian, Dutch, Polish, ...) use free-text or
otherwise unstructured markers that can't be parsed reliably, so they're not
supported here rather than risk silently-wrong results.

Only the *first* noun sense found on a page is used, so a homograph page with
multiple distinct senses of different genders (rare) will only reflect the first.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from . import net


def _identity(word: str) -> str:
    return word


def _capitalize_first(word: str) -> str:
    return word[:1].upper() + word[1:] if word else word


def _extract_de(wikitext: str) -> List[str]:
    match = re.search(r"\{\{Deutsch Substantiv Übersicht(.*?)\}\}", wikitext, re.DOTALL)
    if not match:
        return []
    block = match.group(1)
    letters = re.findall(r"\|\s*Genus(?:\s+\d+)?\s*=\s*([mfn])", block)
    seen: List[str] = []
    for letter in letters:
        if letter not in seen:
            seen.append(letter)
    return seen


def _extract_fr(wikitext: str) -> List[str]:
    idx = wikitext.find("{{S|nom|fr")
    if idx == -1:
        return []
    rest = wikitext[idx + len("{{S|nom|fr") :]
    boundary = re.search(r"\n=+[^=]", rest)
    window = rest[: boundary.start()] if boundary else rest[:2000]
    found = re.findall(r"\{\{(m|f)\}\}", window)
    return found[:1]


_ES_GENDER_PATTERN = re.compile(
    r"\{\{sustantivo (masculino y femenino|femenino y masculino|masculino|femenino)\b"
)


def _extract_es(wikitext: str) -> List[str]:
    match = _ES_GENDER_PATTERN.search(wikitext)
    if not match:
        return []
    label = match.group(1)
    if "masculino" in label and "femenino" in label:
        return ["m", "f"]
    if label == "masculino":
        return ["m"]
    return ["f"]


def _extract_pt(wikitext: str) -> List[str]:
    # {{gramática|...}} is a generic template also used under Adjetivo (e.g. to
    # mark adjective agreement forms), so unlike the other languages it must be
    # scoped to the "Substantivo" (noun) section specifically, or an adjective's
    # own gender-agreement marker gets mistaken for a noun's gender.
    heading = re.search(r"^=+[^=\n]*Substantivo[^=\n]*=+\s*$", wikitext, re.MULTILINE)
    if not heading:
        return []
    rest = wikitext[heading.end() :]
    next_heading = re.search(r"^=+.*=+\s*$", rest, re.MULTILINE)
    window = rest[: next_heading.start()] if next_heading else rest[:2000]
    match = re.search(r"\{\{gram[aá]tica\|([mf])\b", window)
    return [match.group(1)] if match else []


@dataclass
class LanguageSpec:
    code: str
    label: str
    subdomain: str
    normalize: Callable[[str], str]
    extract: Callable[[str], List[str]]
    output_map: dict


SUPPORTED_LANGUAGES: "dict[str, LanguageSpec]" = {
    "de": LanguageSpec("de", "German", "de", _capitalize_first, _extract_de, {"m": "masculine", "f": "feminine", "n": "neuter"}),
    "fr": LanguageSpec("fr", "French", "fr", _identity, _extract_fr, {"m": "masculine", "f": "feminine"}),
    "es": LanguageSpec("es", "Spanish", "es", _identity, _extract_es, {"m": "masculine", "f": "feminine"}),
    "pt": LanguageSpec("pt", "Portuguese", "pt", _identity, _extract_pt, {"m": "masculine", "f": "feminine"}),
}

DEFAULT_LANGUAGE = "de"


def _fetch_wikitext(spec: LanguageSpec, page_title: str) -> Tuple[Optional[str], Optional[str], bool]:
    """Fetch the wikitext for `page_title` on `spec`'s Wiktionary edition.

    Returns (wikitext, error_reason, missing). `missing` is True specifically when
    the page doesn't exist (as opposed to a network/other error), so callers can
    decide whether it's worth retrying under a different casing.
    """
    query = urllib.parse.urlencode(
        {"action": "parse", "page": page_title, "prop": "wikitext", "format": "json", "formatversion": 2}
    )
    url = f"https://{spec.subdomain}.wiktionary.org/w/api.php?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": net.USER_AGENT})

    try:
        with net.open_url(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"{spec.label} Wiktionary HTTP {e.code}: {e.reason}", False
    except urllib.error.URLError as e:
        return None, f"network error reaching {spec.label} Wiktionary: {e.reason}", False
    except Exception as e:
        return None, f"unexpected error calling {spec.label} Wiktionary: {e!r}", False

    if "error" in data:
        code = data["error"].get("code", "")
        if code == "missingtitle":
            return None, f"no {spec.label} Wiktionary page for '{page_title}'", True
        return None, f"{spec.label} Wiktionary error: {data['error'].get('info', code)}", False

    wikitext = data.get("parse", {}).get("wikitext", "")
    if not wikitext:
        return None, f"{spec.label} Wiktionary page for '{page_title}' had no content", False

    return wikitext, None, False


def lookup(word: str, language_code: str) -> Tuple[Optional[str], Optional[str]]:
    """Look up the grammatical gender of `word` on the given language's Wiktionary.

    Returns (gender_value, error_reason). On success error_reason is None.
    On any failure gender_value is None and error_reason describes why.
    """
    if not word:
        return None, "no word to search for"

    spec = SUPPORTED_LANGUAGES.get(language_code)
    if spec is None:
        return None, f"unsupported gender language: {language_code!r}"

    original_word = word.strip()
    query_word = spec.normalize(original_word)

    wikitext, error, missing = _fetch_wikitext(spec, query_word)
    if wikitext is None and missing and query_word != original_word:
        # The normalized casing (e.g. capitalized, for German nouns) wasn't found —
        # try the word as typed, since non-nouns (verbs, adjectives, ...) may use
        # different casing conventions than nouns do in this language.
        wikitext, error, _ = _fetch_wikitext(spec, original_word)

    if wikitext is None:
        return None, error

    letters = spec.extract(wikitext)
    values: List[str] = []
    for letter in letters:
        mapped = spec.output_map.get(letter)
        if mapped and mapped not in values:
            values.append(mapped)

    if not values:
        # The page exists but has no parseable noun-gender template — most likely
        # the word isn't a noun (verb, adjective, ...) rather than a lookup failure,
        # so this is a successful result, not an error.
        return "not-applicable", None

    return "/".join(values), None
