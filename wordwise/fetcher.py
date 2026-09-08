"""Core fetch logic shared by the browser bulk action and the editor button."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from anki.notes import Note

from . import frequency, gender, images


@dataclass
class FetchResult:
    word: str = ""
    image_query: str = ""
    skipped_no_word: bool = False
    frequency_set: bool = False
    frequency_skipped_existing: bool = False
    frequency_not_found: bool = False
    image_set: bool = False
    image_skipped_existing: bool = False
    image_not_found: bool = False
    image_error: Optional[str] = None
    gender_set: bool = False
    gender_skipped_existing: bool = False
    gender_not_found: bool = False
    gender_error: Optional[str] = None
    gender_cleared: bool = False


def fetch_for_note(
    col,
    note: Note,
    profile: dict,
    pexels_api_key: str,
    pixabay_api_key: str,
    overwrite: bool = False,
) -> FetchResult:
    result = FetchResult()

    word = (note[profile["word_field"]] or "").strip()
    result.word = word
    if not word:
        result.skipped_no_word = True
        return result

    freq_field = profile["frequency_field"]
    if note[freq_field].strip() and not overwrite:
        result.frequency_skipped_existing = True
    else:
        freq_value = frequency.lookup(word, profile["frequency_list_path"])
        if freq_value is not None:
            note[freq_field] = freq_value
            result.frequency_set = True
        else:
            result.frequency_not_found = True

    image_field = profile["image_field"]
    if note[image_field].strip() and not overwrite:
        result.image_skipped_existing = True
    else:
        image_search_field = profile.get("image_search_field") or ""
        image_query = word
        if image_search_field:
            image_query = (note[image_search_field] or "").strip() or word
        result.image_query = image_query

        image_bytes, error = images.search_and_download(image_query, pexels_api_key, pixabay_api_key)
        if image_bytes:
            filename = images.save_to_media(col, image_query, image_bytes)
            note[image_field] = f'<img src="{filename}">'
            result.image_set = True
        else:
            result.image_not_found = True
            result.image_error = error

    gender_field = profile.get("gender_field") or ""
    if gender_field:
        if note[gender_field].strip() and not overwrite:
            result.gender_skipped_existing = True
        else:
            language_code = profile.get("gender_language") or gender.DEFAULT_LANGUAGE
            gender_value, gender_err = gender.lookup(word, language_code)
            if gender_value:
                note[gender_field] = gender_value
                result.gender_set = True
            else:
                if note[gender_field] != "":
                    note[gender_field] = ""
                    result.gender_cleared = True
                result.gender_not_found = True
                result.gender_error = gender_err

    return result
