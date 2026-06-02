"""
IceZoom — Focus Shape Overlay Panel (Module C)
Controls the focus vignette: shape, size, background, outline, crosshair.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QSlider, QSpinBox
)

from app.ui.widgets.toggle_switch import ToggleSwitch
from app.ui.widgets.color_picker import ColorOpacityWidget


class FocusPanel(QWidget):
    """
    Module C: Focus Shape Overlay — vignette, outline, crosshair, color controls.
    """

    def __init__(self, profile_manager, overlay_engine, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._oe = overlay_engine
        self._build_ui()
        self._pm.profile_switched.connect(self._refresh)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        heading = QLabel("Focus Shape Overlay")
        heading.setObjectName("heading")
        outer.addWidget(heading)

        sub = QLabel(
            "Configure the focus vignette, outline border, crosshair, and color/opacity settings."
        )
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Content placed directly — the outer QScrollArea is provided by MainWindow
        layout = outer
        layout.setSpacing(12)

        # ── Master Toggle ─────────────────────────────────────────────────────
        layout.addWidget(self._section("OVERLAY"))
        master_card = self._card()
        master_inner = QVBoxLayout(master_card)

        master_row = QHBoxLayout()
        master_row.addWidget(QLabel("Enable Focus Overlay"))
        master_row.addStretch()
        self._master_toggle = ToggleSwitch(self._pm.get("focus_enabled", True))
        self._master_toggle.toggled.connect(self._on_master_toggle)
        master_row.addWidget(self._master_toggle)
        master_inner.addLayout(master_row)
        layout.addWidget(master_card)

        # ── Shape Settings ────────────────────────────────────────────────────
        layout.addWidget(self._section("SHAPE"))
        shape_card = self._card()
        shape_inner = QVBoxLayout(shape_card)
        shape_inner.setSpacing(10)

        # Shape selector
        shape_row = QHBoxLayout()
        shape_row.addWidget(QLabel("Shape"))
        shape_row.addStretch()
        self._shape_combo = QComboBox()
        self._shape_combo.addItems(["Circle", "Square"])
        self._shape_combo.setCurrentText(self._pm.get("focus_shape", "Circle"))
        self._shape_combo.currentTextChanged.connect(
            lambda v: (self._pm.set("focus_shape", v), self._oe.update())
        )
        shape_row.addWidget(self._shape_combo)
        shape_inner.addLayout(shape_row)

        # Size slider
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size"))
        size_row.addStretch()
        self._size_val_lbl = QLabel(f"{self._pm.get('focus_size', 300)}px")
        self._size_val_lbl.setObjectName("value_label")
        size_row.addWidget(self._size_val_lbl)
        shape_inner.addLayout(size_row)

        self._size_slider = QSlider(Qt.Orientation.Horizontal)
        self._size_slider.setRange(80, 800)
        self._size_slider.setValue(self._pm.get("focus_size", 300))
        self._size_slider.valueChanged.connect(self._on_size_changed)
        shape_inner.addWidget(self._size_slider)

        layout.addWidget(shape_card)

        # ── Background ────────────────────────────────────────────────────────
        layout.addWidget(self._section("BACKGROUND DIM"))
        bg_card = self._card()
        bg_inner = QVBoxLayout(bg_card)
        bg_inner.setSpacing(10)

        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel("Dim Background"))
        bg_row.addStretch()
        self._bg_toggle = ToggleSwitch(self._pm.get("focus_bg_enabled", True))
        self._bg_toggle.toggled.connect(
            lambda v: (self._pm.set("focus_bg_enabled", v), self._oe.update())
        )
        bg_row.addWidget(self._bg_toggle)
        bg_inner.addLayout(bg_row)

        bg_color_row = QHBoxLayout()
        bg_color_row.addWidget(QLabel("Color & Opacity"))
        bg_color_row.addStretch()
        self._bg_color = ColorOpacityWidget(
            self._pm.get("focus_bg_color", "#000000"),
            self._pm.get("focus_bg_opacity", 0.55)
        )
        self._bg_color.color_changed.connect(self._on_bg_color_changed)
        bg_color_row.addWidget(self._bg_color)
        bg_inner.addLayout(bg_color_row)

        layout.addWidget(bg_card)

        # ── Outline ───────────────────────────────────────────────────────────
        layout.addWidget(self._section("OUTLINE BORDER"))
        outline_card = self._card()
        outline_inner = QVBoxLayout(outline_card)
        outline_inner.setSpacing(10)

        outline_row = QHBoxLayout()
        outline_row.addWidget(QLabel("Show Outline"))
        outline_row.addStretch()
        self._outline_toggle = ToggleSwitch(self._pm.get("focus_outline_enabled", True))
        self._outline_toggle.toggled.connect(
            lambda v: (self._pm.set("focus_outline_enabled", v), self._oe.update())
        )
        outline_row.addWidget(self._outline_toggle)
        outline_inner.addLayout(outline_row)

        outline_color_row = QHBoxLayout()
        outline_color_row.addWidget(QLabel("Color & Opacity"))
        outline_color_row.addStretch()
        self._outline_color = ColorOpacityWidget(
            self._pm.get("focus_outline_color", "#00D4FF"),
            self._pm.get("focus_outline_opacity", 1.0)
        )
        self._outline_color.color_changed.connect(self._on_outline_color_changed)
        outline_color_row.addWidget(self._outline_color)
        outline_inner.addLayout(outline_color_row)

        # Width
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Border Width"))
        width_row.addStretch()
        self._outline_width = QSpinBox()
        self._outline_width.setRange(1, 20)
        self._outline_width.setValue(self._pm.get("focus_outline_width", 3))
        self._outline_width.valueChanged.connect(
            lambda v: (self._pm.set("focus_outline_width", v), self._oe.update())
        )
        width_row.addWidget(self._outline_width)
        outline_inner.addLayout(width_row)

        layout.addWidget(outline_card)

        # ── Crosshair ─────────────────────────────────────────────────────────
        layout.addWidget(self._section("CROSSHAIR"))
        ch_card = self._card()
        ch_inner = QVBoxLayout(ch_card)
        ch_inner.setSpacing(10)

        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Show Crosshair"))
        ch_row.addStretch()
        self._ch_toggle = ToggleSwitch(self._pm.get("crosshair_enabled", False))
        self._ch_toggle.toggled.connect(
            lambda v: (self._pm.set("crosshair_enabled", v), self._oe.update())
        )
        ch_row.addWidget(self._ch_toggle)
        ch_inner.addLayout(ch_row)

        ch_color_row = QHBoxLayout()
        ch_color_row.addWidget(QLabel("Color & Opacity"))
        ch_color_row.addStretch()
        self._ch_color = ColorOpacityWidget(
            self._pm.get("crosshair_color", "#FF4444"),
            self._pm.get("crosshair_opacity", 0.9)
        )
        self._ch_color.color_changed.connect(self._on_ch_color_changed)
        ch_color_row.addWidget(self._ch_color)
        ch_inner.addLayout(ch_color_row)

        # Size
        ch_size_row = QHBoxLayout()
        ch_size_row.addWidget(QLabel("Crosshair Size"))
        ch_size_row.addStretch()
        self._ch_size = QSpinBox()
        self._ch_size.setRange(4, 100)
        self._ch_size.setValue(self._pm.get("crosshair_size", 20))
        self._ch_size.valueChanged.connect(
            lambda v: (self._pm.set("crosshair_size", v), self._oe.update())
        )
        ch_size_row.addWidget(self._ch_size)
        ch_inner.addLayout(ch_size_row)

        # Thickness
        ch_thick_row = QHBoxLayout()
        ch_thick_row.addWidget(QLabel("Line Thickness"))
        ch_thick_row.addStretch()
        self._ch_thick = QSpinBox()
        self._ch_thick.setRange(1, 10)
        self._ch_thick.setValue(self._pm.get("crosshair_thickness", 2))
        self._ch_thick.valueChanged.connect(
            lambda v: (self._pm.set("crosshair_thickness", v), self._oe.update())
        )
        ch_thick_row.addWidget(self._ch_thick)
        ch_inner.addLayout(ch_thick_row)

        layout.addWidget(ch_card)
        layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section_title")
        return lbl

    def _card(self) -> QFrame:
        f = QFrame()
        f.setObjectName("card")
        return f

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_master_toggle(self, enabled: bool):
        self._pm.set("focus_enabled", enabled)
        self._oe.set_visible(enabled and self._oe._visible)
        self._oe.update()

    def _on_size_changed(self, value: int):
        self._size_val_lbl.setText(f"{value}px")
        self._pm.set("focus_size", value)
        self._oe.update()

    def _on_bg_color_changed(self, color: str, opacity: float):
        self._pm.set("focus_bg_color", color)
        self._pm.set("focus_bg_opacity", opacity)
        self._oe.update()

    def _on_outline_color_changed(self, color: str, opacity: float):
        self._pm.set("focus_outline_color", color)
        self._pm.set("focus_outline_opacity", opacity)
        self._oe.update()

    def _on_ch_color_changed(self, color: str, opacity: float):
        self._pm.set("crosshair_color", color)
        self._pm.set("crosshair_opacity", opacity)
        self._oe.update()

    def _refresh(self, _name: str = ""):
        self._master_toggle.setChecked(self._pm.get("focus_enabled", True))
        self._shape_combo.blockSignals(True)
        self._shape_combo.setCurrentText(self._pm.get("focus_shape", "Circle"))
        self._shape_combo.blockSignals(False)

        size = self._pm.get("focus_size", 300)
        self._size_slider.blockSignals(True)
        self._size_slider.setValue(size)
        self._size_val_lbl.setText(f"{size}px")
        self._size_slider.blockSignals(False)

        self._bg_toggle.setChecked(self._pm.get("focus_bg_enabled", True))
        self._bg_color.set_color(self._pm.get("focus_bg_color", "#000000"))
        self._bg_color.set_opacity(self._pm.get("focus_bg_opacity", 0.55))

        self._outline_toggle.setChecked(self._pm.get("focus_outline_enabled", True))
        self._outline_color.set_color(self._pm.get("focus_outline_color", "#00D4FF"))
        self._outline_color.set_opacity(self._pm.get("focus_outline_opacity", 1.0))
        self._outline_width.blockSignals(True)
        self._outline_width.setValue(self._pm.get("focus_outline_width", 3))
        self._outline_width.blockSignals(False)

        self._ch_toggle.setChecked(self._pm.get("crosshair_enabled", False))
        self._ch_color.set_color(self._pm.get("crosshair_color", "#FF4444"))
        self._ch_color.set_opacity(self._pm.get("crosshair_opacity", 0.9))
        self._ch_size.blockSignals(True)
        self._ch_size.setValue(self._pm.get("crosshair_size", 20))
        self._ch_size.blockSignals(False)
        self._ch_thick.blockSignals(True)
        self._ch_thick.setValue(self._pm.get("crosshair_thickness", 2))
        self._ch_thick.blockSignals(False)
