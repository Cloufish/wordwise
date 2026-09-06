"""Wordwise: fetch word frequency and a memory-aid image into Anki notes."""

from aqt import mw
from aqt.qt import QAction

from . import browser_action, editor_button
from .settings_dialog import open_settings_dialog

_settings_action = QAction("Wordwise Settings…", mw)
_settings_action.triggered.connect(open_settings_dialog)
mw.form.menuTools.addAction(_settings_action)

# Make the "Config" button in Tools > Add-ons open the same dialog,
# instead of Anki's raw JSON config editor.
mw.addonManager.setConfigAction(__name__, open_settings_dialog)

browser_action.setup()
editor_button.setup()
