"""Browser bulk-fetch action: select notes, fetch frequency & image for all of them."""

from __future__ import annotations

from dataclasses import dataclass

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.operations import QueryOp
from aqt.qt import QAction
from aqt.utils import showInfo, showWarning

from . import config_schema, fetcher


@dataclass
class BulkSummary:
    notes_touched: int = 0
    updated_frequency: int = 0
    updated_image: int = 0
    not_found_frequency: int = 0
    not_found_image: int = 0
    skipped_no_word: int = 0
    skipped_no_profile: int = 0
    last_image_error: str = ""
    updated_gender: int = 0
    not_found_gender: int = 0
    last_gender_error: str = ""
    cancelled: bool = False
    notes_processed: int = 0


def _update_progress(label: str, value: int, max_: int) -> None:
    # Progress reporting is a nice-to-have, not core to the fetch itself — never
    # let a problem here (e.g. an Anki version quirk) abort the whole operation.
    try:
        mw.taskman.run_on_main(lambda: mw.progress.update(label=label, value=value, max=max_))
    except Exception:
        pass


def _want_cancel() -> bool:
    try:
        return mw.progress.want_cancel()
    except Exception:
        return False


def _run_bulk_fetch(col, note_ids, cfg) -> BulkSummary:
    summary = BulkSummary()
    total = len(note_ids)
    for i, nid in enumerate(note_ids, start=1):
        if _want_cancel():
            summary.cancelled = True
            break

        note = col.get_note(nid)
        note_type_name = note.note_type()["name"]
        profile = config_schema.find_profile(cfg, note_type_name)

        preview_word = (note[profile["word_field"]] or "").strip() if profile else ""
        label = f"Wordwise: note {i}/{total}" + (f" — {preview_word}" if preview_word else "")
        _update_progress(label, i, total)

        summary.notes_processed += 1
        if profile is None:
            summary.skipped_no_profile += 1
            continue

        result = fetcher.fetch_for_note(
            col,
            note,
            profile,
            cfg["pexels_api_key"],
            cfg["pixabay_api_key"],
            overwrite=cfg.get("overwrite_existing", False),
        )
        if result.skipped_no_word:
            summary.skipped_no_word += 1
            continue

        if result.frequency_set or result.image_set or result.gender_set or result.gender_cleared:
            col.update_note(note)
            summary.notes_touched += 1
        if result.frequency_set:
            summary.updated_frequency += 1
        if result.frequency_not_found:
            summary.not_found_frequency += 1
        if result.image_set:
            summary.updated_image += 1
        if result.image_not_found:
            summary.not_found_image += 1
            if result.image_error:
                summary.last_image_error = result.image_error
        if result.gender_set:
            summary.updated_gender += 1
        if result.gender_not_found:
            summary.not_found_gender += 1
            if result.gender_error:
                summary.last_gender_error = result.gender_error
    return summary


def _on_success(browser: Browser, summary: BulkSummary, overwrite: bool, total: int) -> None:
    browser.table.reset()
    mode = "overwrite existing values" if overwrite else "skip existing values"
    heading = (
        f"Wordwise fetch cancelled after {summary.notes_processed}/{total} notes."
        if summary.cancelled
        else "Wordwise fetch complete."
    )
    text = (
        f"{heading}\n\n"
        f"Mode: {mode}\n"
        f"Notes updated: {summary.notes_touched}\n"
        f"Frequency set: {summary.updated_frequency}  (not found: {summary.not_found_frequency})\n"
        f"Image set: {summary.updated_image}  (not found: {summary.not_found_image})\n"
        f"Gender set: {summary.updated_gender}  (not found: {summary.not_found_gender})\n"
        f"Skipped (empty word field): {summary.skipped_no_word}\n"
        f"Skipped (no profile for note type): {summary.skipped_no_profile}"
    )
    if summary.last_image_error:
        text += f"\n\nLast image error seen: {summary.last_image_error}"
    if summary.last_gender_error:
        text += f"\n\nLast gender error seen: {summary.last_gender_error}"
    showInfo(text)


def _fetch_selected(browser: Browser) -> None:
    note_ids = browser.selected_notes()
    if not note_ids:
        showWarning("No notes selected.")
        return

    cfg = config_schema.get_config()
    if not cfg["profiles"]:
        showWarning("No Wordwise profiles configured. Use Tools ▸ Wordwise Settings… first.")
        return
    if not cfg["pexels_api_key"] and not cfg["pixabay_api_key"]:
        showWarning(
            "No Pexels or Pixabay API key configured. Frequency will still be fetched, "
            "but images will be skipped until you add at least one key in Tools ▸ Wordwise Settings…."
        )

    overwrite = cfg.get("overwrite_existing", False)
    total = len(note_ids)
    QueryOp(
        parent=browser,
        op=lambda col: _run_bulk_fetch(col, note_ids, cfg),
        success=lambda summary: _on_success(browser, summary, overwrite, total),
    ).with_progress("Wordwise: fetching frequency, images & gender…").run_in_background()


def _on_browser_menus_did_init(browser: Browser) -> None:
    action = QAction("Wordwise: Fetch Frequency, Image && Gender", browser)
    action.triggered.connect(lambda: _fetch_selected(browser))
    browser.form.menu_Notes.addAction(action)


def setup() -> None:
    gui_hooks.browser_menus_did_init.append(_on_browser_menus_did_init)
