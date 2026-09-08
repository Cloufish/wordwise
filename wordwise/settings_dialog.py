"""Tools > Wordwise Settings... dialog: image provider keys + per-Note-Type profiles."""

from __future__ import annotations

from typing import Optional

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    Qt,
    QVBoxLayout,
)
from aqt.utils import showWarning

from . import config_schema, gender

_SAME_AS_WORD_FIELD = "(same as Word field)"
_NO_GENDER = "(none — don't fetch gender)"


def _profile_label(profile: dict) -> str:
    image_search_field = profile.get("image_search_field") or ""
    image_source = f"{image_search_field} (image search)" if image_search_field else profile["word_field"]
    label = (
        f'{profile["note_type"]}  '
        f'(word: {profile["word_field"]} → '
        f'freq: {profile["frequency_field"]}, image: {profile["image_field"]} '
        f'[search: {image_source}]'
    )
    gender_field = profile.get("gender_field") or ""
    if gender_field:
        language_code = profile.get("gender_language") or gender.DEFAULT_LANGUAGE
        label += f", gender: {gender_field} [{language_code}]"
    return label + ")"


class ProfileEditDialog(QDialog):
    def __init__(self, parent, profile: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Wordwise Profile")
        self.profile = dict(profile) if profile else None

        self.note_type_combo = QComboBox()
        self.note_type_combo.addItems(sorted(mw.col.models.all_names()))
        self.note_type_combo.currentTextChanged.connect(self._reload_fields)

        self.word_field_combo = QComboBox()
        self.frequency_field_combo = QComboBox()
        self.image_field_combo = QComboBox()
        self.image_search_field_combo = QComboBox()
        self.gender_field_combo = QComboBox()

        self.gender_language_edit = QLineEdit()
        self.gender_language_edit.setPlaceholderText("e.g. de, fr, es, ja, ru…")

        self.path_edit = QLineEdit()
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Note Type:"))
        layout.addWidget(self.note_type_combo)
        layout.addWidget(QLabel("Word field (source):"))
        layout.addWidget(self.word_field_combo)
        layout.addWidget(QLabel("Frequency field (target):"))
        layout.addWidget(self.frequency_field_combo)
        layout.addWidget(QLabel("Image field (target):"))
        layout.addWidget(self.image_field_combo)
        layout.addWidget(QLabel("Image search field (optional — e.g. an English translation, since\nPexels/Pixabay tend to return better results in English; leave as\n\"(same as Word field)\" to search using the Word field):"))
        layout.addWidget(self.image_search_field_combo)
        layout.addWidget(QLabel("Gender field (optional — target field for noun gender):"))
        layout.addWidget(self.gender_field_combo)
        layout.addWidget(QLabel("Gender language (ISO 639-1 code, e.g. \"de\" — used to look up the\nWord field on freedictionaryapi.com):"))
        layout.addWidget(self.gender_language_edit)
        layout.addWidget(QLabel("Frequency list file (Hermit Dave .txt):"))
        layout.addLayout(path_row)
        layout.addWidget(buttons)
        self.setLayout(layout)

        if self.profile:
            self.note_type_combo.setCurrentText(self.profile["note_type"])
            self._reload_fields(self.profile["note_type"])
            self.word_field_combo.setCurrentText(self.profile["word_field"])
            self.frequency_field_combo.setCurrentText(self.profile["frequency_field"])
            self.image_field_combo.setCurrentText(self.profile["image_field"])
            self.image_search_field_combo.setCurrentText(
                self.profile.get("image_search_field") or _SAME_AS_WORD_FIELD
            )
            self.gender_field_combo.setCurrentText(self.profile.get("gender_field") or _NO_GENDER)
            self.gender_language_edit.setText(self.profile.get("gender_language") or gender.DEFAULT_LANGUAGE)
            self.path_edit.setText(self.profile["frequency_list_path"])
        else:
            self.gender_language_edit.setText(gender.DEFAULT_LANGUAGE)
            if self.note_type_combo.count():
                self._reload_fields(self.note_type_combo.currentText())

    def _reload_fields(self, note_type_name: str) -> None:
        for combo in (
            self.word_field_combo,
            self.frequency_field_combo,
            self.image_field_combo,
            self.image_search_field_combo,
            self.gender_field_combo,
        ):
            combo.clear()
        self.image_search_field_combo.addItem(_SAME_AS_WORD_FIELD)
        self.gender_field_combo.addItem(_NO_GENDER)
        if not note_type_name:
            return
        notetype = mw.col.models.by_name(note_type_name)
        if not notetype:
            return
        field_names = mw.col.models.field_names(notetype)
        for combo in (self.word_field_combo, self.frequency_field_combo, self.image_field_combo):
            combo.addItems(field_names)
        self.image_search_field_combo.addItems(field_names)
        self.gender_field_combo.addItems(field_names)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select frequency list file", "", "Text files (*.txt);;All files (*)")
        if path:
            self.path_edit.setText(path)

    def _accept(self) -> None:
        if not self.note_type_combo.currentText():
            showWarning("Choose a Note Type.")
            return
        if not self.path_edit.text().strip():
            showWarning("Choose a frequency list file.")
            return
        image_search_field = self.image_search_field_combo.currentText()
        if image_search_field == _SAME_AS_WORD_FIELD:
            image_search_field = ""

        gender_field = self.gender_field_combo.currentText()
        if gender_field == _NO_GENDER:
            gender_field = ""

        self.result_profile = {
            "note_type": self.note_type_combo.currentText(),
            "word_field": self.word_field_combo.currentText(),
            "frequency_field": self.frequency_field_combo.currentText(),
            "image_field": self.image_field_combo.currentText(),
            "image_search_field": image_search_field,
            "gender_field": gender_field,
            "gender_language": self.gender_language_edit.text().strip() or gender.DEFAULT_LANGUAGE,
            "frequency_list_path": self.path_edit.text().strip(),
        }
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Wordwise Settings")
        self.setMinimumWidth(480)

        self.cfg = config_schema.get_config()

        self.pexels_api_key_edit = QLineEdit(self.cfg["pexels_api_key"])
        self.pexels_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.pixabay_api_key_edit = QLineEdit(self.cfg["pixabay_api_key"])
        self.pixabay_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.overwrite_checkbox = QCheckBox("Overwrite existing Frequency/Image field content when fetching")
        self.overwrite_checkbox.setChecked(self.cfg.get("overwrite_existing", False))

        self.profile_list = QListWidget()
        self._reload_profile_list()

        add_btn = QPushButton("Add…")
        edit_btn = QPushButton("Edit…")
        remove_btn = QPushButton("Remove")
        add_btn.clicked.connect(self._add_profile)
        edit_btn.clicked.connect(self._edit_profile)
        remove_btn.clicked.connect(self._remove_profile)

        profile_btn_row = QHBoxLayout()
        profile_btn_row.addWidget(add_btn)
        profile_btn_row.addWidget(edit_btn)
        profile_btn_row.addWidget(remove_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Pexels API key (primary image source):"))
        layout.addWidget(self.pexels_api_key_edit)
        layout.addWidget(QLabel("Pixabay API key (fallback, used when Pexels finds nothing):"))
        layout.addWidget(self.pixabay_api_key_edit)
        layout.addWidget(self.overwrite_checkbox)
        layout.addWidget(QLabel("Note Type profiles:"))
        layout.addWidget(self.profile_list)
        layout.addLayout(profile_btn_row)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _reload_profile_list(self) -> None:
        self.profile_list.clear()
        for profile in self.cfg["profiles"]:
            item = QListWidgetItem(_profile_label(profile))
            item.setData(Qt.ItemDataRole.UserRole, profile)
            self.profile_list.addItem(item)

    def _add_profile(self) -> None:
        dlg = ProfileEditDialog(self)
        if dlg.exec():
            self.cfg["profiles"].append(dlg.result_profile)
            self._reload_profile_list()

    def _edit_profile(self) -> None:
        row = self.profile_list.currentRow()
        if row < 0:
            return
        dlg = ProfileEditDialog(self, self.cfg["profiles"][row])
        if dlg.exec():
            self.cfg["profiles"][row] = dlg.result_profile
            self._reload_profile_list()

    def _remove_profile(self) -> None:
        row = self.profile_list.currentRow()
        if row < 0:
            return
        del self.cfg["profiles"][row]
        self._reload_profile_list()

    def _save(self) -> None:
        self.cfg["pexels_api_key"] = self.pexels_api_key_edit.text().strip()
        self.cfg["pixabay_api_key"] = self.pixabay_api_key_edit.text().strip()
        self.cfg["overwrite_existing"] = self.overwrite_checkbox.isChecked()
        config_schema.write_config(self.cfg)
        self.accept()


def open_settings_dialog() -> None:
    SettingsDialog(mw).exec()
