"""Editor toolbar button: fetch frequency & image for the single note being edited."""

from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.utils import showWarning, tooltip

from . import config_schema, fetcher


def _on_success(editor: Editor, result: fetcher.FetchResult) -> None:
    if result.skipped_no_word:
        tooltip("Wordwise: word field is empty, nothing to fetch.")
        return

    if editor.note.id:
        mw.col.update_note(editor.note)
    editor.loadNoteKeepingFocus()

    parts = []
    if result.frequency_set:
        parts.append("frequency set")
    if result.image_set:
        parts.append("image set")
    if result.gender_set:
        parts.append("gender set")
    if not parts:
        errors = [e for e in (result.image_error, result.gender_error) if e]
        if errors:
            parts.append("failed (" + "; ".join(errors) + ")")
        else:
            parts.append("nothing new (already filled or not found)")
    tooltip("Wordwise: " + ", ".join(parts))


def _fetch_current_note(editor: Editor) -> None:
    note = editor.note
    if note is None:
        return

    note_type_name = note.note_type()["name"]
    cfg = config_schema.get_config()
    profile = config_schema.find_profile(cfg, note_type_name)
    if profile is None:
        showWarning(
            f'No Wordwise profile configured for note type "{note_type_name}". '
            "Use Tools ▸ Wordwise Settings… to add one."
        )
        return

    overwrite = cfg.get("overwrite_existing", False)
    QueryOp(
        parent=editor.parentWindow,
        op=lambda col: fetcher.fetch_for_note(col, note, profile, cfg["pexels_api_key"], overwrite=overwrite),
        success=lambda result: _on_success(editor, result),
    ).with_progress("Wordwise: fetching frequency, image & gender…").run_in_background()


def _on_editor_did_init_buttons(buttons: list, editor: Editor) -> None:
    button = editor.addButton(
        icon=None,
        cmd="wordwise_fetch",
        func=_fetch_current_note,
        tip="Wordwise: Fetch Frequency, Image & Gender",
        label="WW",
    )
    buttons.append(button)


def setup() -> None:
    gui_hooks.editor_did_init_buttons.append(_on_editor_did_init_buttons)
