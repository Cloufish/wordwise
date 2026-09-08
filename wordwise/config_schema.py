"""Config read/write helpers for the Wordwise add-on."""

from __future__ import annotations

from typing import Optional, TypedDict

from aqt import mw

from . import gender


class Profile(TypedDict):
    note_type: str
    word_field: str
    frequency_field: str
    image_field: str
    frequency_list_path: str
    # Optional: field to search for images with instead of word_field (e.g. an
    # English translation, since both image providers tend to return better
    # results for English queries than for other languages). Empty string means
    # "use word_field". Missing on profiles saved before this option existed.
    image_search_field: str
    # Optional: field to write the noun's grammatical gender to (looked up via
    # gender.lookup using word_field). Empty string means gender fetching is
    # disabled for this profile.
    gender_field: str
    # Free-text ISO 639-1/639-3 language code (e.g. "de", "fr", "ja") passed to
    # freedictionaryapi.com. Only meaningful when gender_field is set.
    gender_language: str


class Config(TypedDict):
    # Primary image source. Pixabay is used as a fallback when Pexels finds
    # nothing (missing key, no results, or a request error).
    pexels_api_key: str
    pixabay_api_key: str
    profiles: list
    # When True, fetching overwrites Frequency/Image fields that already have
    # content instead of skipping them.
    overwrite_existing: bool


def get_config() -> Config:
    cfg = mw.addonManager.getConfig(__name__.split(".")[0])
    if cfg is None:
        cfg = {"pexels_api_key": "", "pixabay_api_key": "", "profiles": []}
    cfg.setdefault("pexels_api_key", "")
    cfg.setdefault("pixabay_api_key", "")
    cfg.setdefault("profiles", [])
    cfg.setdefault("overwrite_existing", False)
    for profile in cfg["profiles"]:
        profile.setdefault("image_search_field", "")
        profile.setdefault("gender_field", "")
        profile.setdefault("gender_language", gender.DEFAULT_LANGUAGE)
    return cfg


def write_config(cfg: Config) -> None:
    mw.addonManager.writeConfig(__name__.split(".")[0], cfg)


def find_profile(cfg: Config, note_type_name: str) -> Optional[Profile]:
    for profile in cfg["profiles"]:
        if profile["note_type"] == note_type_name:
            return profile
    return None
