"""
IceZoom — Profile Panel
Sidebar module for creating, deleting, duplicating, renaming profiles
and managing auto-switch app associations.
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QFrame, QInputDialog,
    QMessageBox, QFileDialog, QGroupBox
)

from app.utils.constants import ICE_BLUE


class ProfilePanel(QWidget):
    """
    Full profile management UI:
    - List of profiles with active highlight
    - Add / Delete / Duplicate / Rename
    - Auto-switch app manager
    - Export / Import bundle
    """
    profile_selected = pyqtSignal(str)

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._build_ui()
        self._refresh_list()

        self._pm.profiles_changed.connect(self._refresh_list)
        self._pm.profile_switched.connect(self._on_profile_switched)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────────────
        heading = QLabel("Configuration Profiles")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        sub = QLabel("Each profile stores all settings, hotkeys, and preferences independently.")
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # ── Profile List ──────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setMinimumHeight(160)
        self._list.currentTextChanged.connect(self._on_select)
        layout.addWidget(self._list)

        # ── Action Buttons ────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self._add_btn = QPushButton("＋ New")
        self._add_btn.setObjectName("primary")
        self._add_btn.setToolTip("Create a new profile")
        self._add_btn.clicked.connect(self._create_profile)
        btn_layout.addWidget(self._add_btn)

        self._dup_btn = QPushButton("⧉ Duplicate")
        self._dup_btn.setToolTip("Duplicate selected profile")
        self._dup_btn.clicked.connect(self._duplicate_profile)
        btn_layout.addWidget(self._dup_btn)

        layout.addLayout(btn_layout)

        btn2_layout = QHBoxLayout()
        btn2_layout.setSpacing(6)

        self._ren_btn = QPushButton("✎ Rename")
        self._ren_btn.setToolTip("Rename selected profile")
        self._ren_btn.clicked.connect(self._rename_profile)
        btn2_layout.addWidget(self._ren_btn)

        self._del_btn = QPushButton("🗑 Delete")
        self._del_btn.setObjectName("danger")
        self._del_btn.setToolTip("Delete selected profile")
        self._del_btn.clicked.connect(self._delete_profile)
        btn2_layout.addWidget(self._del_btn)

        layout.addLayout(btn2_layout)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # ── Auto-Switch Apps ──────────────────────────────────────────────────
        auto_label = QLabel("AUTO-SWITCH APPS")
        auto_label.setObjectName("section_title")
        layout.addWidget(auto_label)

        auto_desc = QLabel("This profile activates when any listed .exe gains focus.")
        auto_desc.setObjectName("muted")
        auto_desc.setWordWrap(True)
        layout.addWidget(auto_desc)

        self._app_list = QListWidget()
        self._app_list.setMaximumHeight(100)
        layout.addWidget(self._app_list)

        app_btn_layout = QHBoxLayout()
        app_btn_layout.setSpacing(6)

        self._app_add_btn = QPushButton("＋ Add EXE")
        self._app_add_btn.clicked.connect(self._add_app)
        app_btn_layout.addWidget(self._app_add_btn)

        self._app_del_btn = QPushButton("Remove")
        self._app_del_btn.setObjectName("danger")
        self._app_del_btn.clicked.connect(self._remove_app)
        app_btn_layout.addWidget(self._app_del_btn)

        layout.addLayout(app_btn_layout)

        # ── Separator ─────────────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setObjectName("separator")
        layout.addWidget(sep2)

        # ── Import / Export ───────────────────────────────────────────────────
        io_label = QLabel("IMPORT / EXPORT")
        io_label.setObjectName("section_title")
        layout.addWidget(io_label)

        io_layout = QHBoxLayout()
        io_layout.setSpacing(6)

        exp_btn = QPushButton("⬆ Export All")
        exp_btn.setToolTip("Save all profiles as .icezoom bundle")
        exp_btn.clicked.connect(self._export)
        io_layout.addWidget(exp_btn)

        imp_btn = QPushButton("⬇ Import")
        imp_btn.setToolTip("Load profiles from .icezoom bundle")
        imp_btn.clicked.connect(self._import)
        io_layout.addWidget(imp_btn)

        layout.addLayout(io_layout)
        layout.addStretch()

    # ── Profile List ──────────────────────────────────────────────────────────

    def _refresh_list(self):
        self._list.blockSignals(True)
        self._list.clear()
        active = self._pm.active_name()
        for name in self._pm.list_profiles():
            item = QListWidgetItem(name)
            if name == active:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.cyan)
            self._list.addItem(item)
        # Select active
        items = self._list.findItems(active, Qt.MatchFlag.MatchExactly)
        if items:
            self._list.setCurrentItem(items[0])
        self._list.blockSignals(False)
        self._refresh_apps()

    def _on_select(self, name: str):
        if name and name != self._pm.active_name():
            self._pm.switch(name)
            self.profile_selected.emit(name)
            self._refresh_list()

    def _on_profile_switched(self, name: str):
        self._refresh_list()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _create_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name.strip():
            if not self._pm.create(name.strip()):
                QMessageBox.warning(self, "IceZoom", f"Profile '{name}' already exists.")
            else:
                self._pm.switch(name.strip())

    def _duplicate_profile(self):
        current = self._list.currentItem()
        if not current:
            return
        name = current.text()
        new_name, ok = QInputDialog.getText(
            self, "Duplicate Profile", "New profile name:", text=f"{name} (Copy)"
        )
        if ok and new_name.strip():
            if not self._pm.duplicate(name, new_name.strip()):
                QMessageBox.warning(self, "IceZoom", "Could not duplicate profile.")

    def _rename_profile(self):
        current = self._list.currentItem()
        if not current:
            return
        old_name = current.text()
        new_name, ok = QInputDialog.getText(
            self, "Rename Profile", "New name:", text=old_name
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            if not self._pm.rename(old_name, new_name.strip()):
                QMessageBox.warning(self, "IceZoom", "Could not rename profile.")

    def _delete_profile(self):
        current = self._list.currentItem()
        if not current:
            return
        name = current.text()
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Are you sure you want to delete '{name}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            if not self._pm.delete(name):
                QMessageBox.warning(self, "IceZoom", "Cannot delete the last remaining profile.")

    # ── Auto-switch Apps ──────────────────────────────────────────────────────

    def _refresh_apps(self):
        self._app_list.clear()
        for exe in self._pm.get("auto_switch_apps", []):
            self._app_list.addItem(exe)

    def _add_app(self):
        exe, ok = QInputDialog.getText(
            self, "Add Auto-Switch App",
            "Enter the executable name (e.g. minecraft.exe):"
        )
        if ok and exe.strip():
            self._pm.add_auto_switch_app(exe.strip())
            self._refresh_apps()

    def _remove_app(self):
        current = self._app_list.currentItem()
        if current:
            self._pm.remove_auto_switch_app(current.text())
            self._refresh_apps()

    # ── Import / Export ───────────────────────────────────────────────────────

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profiles", "icezoom_profiles.icezoom",
            "IceZoom Bundle (*.icezoom)"
        )
        if path:
            try:
                self._pm.export_all(path)
                QMessageBox.information(self, "IceZoom", f"Profiles exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Profiles", "",
            "IceZoom Bundle (*.icezoom)"
        )
        if path:
            try:
                self._pm.import_bundle(path)
                QMessageBox.information(self, "IceZoom", "Profiles imported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", str(e))
