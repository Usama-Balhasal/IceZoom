"""
IceZoom — Hotkey Panel (Module A)
Displays and records global hotkey bindings per profile.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)

from app.utils.constants import HOTKEY_DEFAULTS
from app.ui.widgets.hotkey_widget import HotkeyWidget


class HotkeyPanel(QWidget):
    """
    Module A: Controls & Hotkeys
    Each hotkey row shows the action name, description, and HotkeyWidget.
    """

    def __init__(self, profile_manager, hotkey_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._hm = hotkey_manager
        self._widgets: dict[str, HotkeyWidget] = {}
        self._build_ui()

        self._pm.profile_switched.connect(self._refresh)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        heading = QLabel("Controls & Hotkeys")
        heading.setObjectName("heading")
        outer.addWidget(heading)

        sub = QLabel(
            "Click any binding badge to re-record. Changes apply instantly to the active profile."
        )
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # ── Scroll area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)

        hotkeys = self._pm.get("hotkeys", {})

        for hd in HOTKEY_DEFAULTS:
            combo = hotkeys.get(hd.action_id, hd.default_combo)
            row = self._make_row(hd, combo)
            layout.addWidget(row)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _make_row(self, hd, combo: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        row_layout = QVBoxLayout(card)
        row_layout.setContentsMargins(16, 12, 16, 12)
        row_layout.setSpacing(6)

        # Top: name + hold badge
        top = QHBoxLayout()
        name_lbl = QLabel(hd.display_name)
        name_lbl.setStyleSheet("font-weight: 700; font-size: 14px;")
        top.addWidget(name_lbl)

        if hd.hold_mode:
            hold_badge = QLabel(" HOLD ")
            hold_badge.setStyleSheet("""
                background: #1A3040; color: #00D4FF;
                border: 1px solid #00D4FF; border-radius: 4px;
                font-size: 10px; font-weight: 700; padding: 2px 6px;
            """)
            top.addWidget(hold_badge)

        top.addStretch()
        row_layout.addLayout(top)

        # Description
        desc_lbl = QLabel(hd.description)
        desc_lbl.setObjectName("muted")
        row_layout.addWidget(desc_lbl)

        # HotkeyWidget
        hw = HotkeyWidget(hd.action_id, combo)
        hw.combo_changed.connect(self._on_combo_changed)
        self._widgets[hd.action_id] = hw
        row_layout.addWidget(hw)

        return card

    def _on_combo_changed(self, action_id: str, combo: str):
        self._pm.set_hotkey(action_id, combo)
        self._hm.update_binding(action_id, combo)

    def _refresh(self, _name: str = ""):
        hotkeys = self._pm.get("hotkeys", {})
        for action_id, widget in self._widgets.items():
            combo = hotkeys.get(action_id, "")
            widget.set_combo(combo)
        # Reload all hotkeys from the new profile
        self._hm.load_bindings(hotkeys)
