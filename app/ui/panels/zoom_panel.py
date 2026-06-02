"""
IceZoom — Zoom Behavior Panel (Module B)
Controls zoom mode, factor, animations, sensitivity, PiP, coordinates.
"""
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QGroupBox
)

from app.ui.widgets.toggle_switch import ToggleSwitch


class ZoomPanel(QWidget):
    """
    Module B: Zoom Behavior & Physics
    """

    def __init__(self, profile_manager, zoom_engine, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._ze = zoom_engine
        self._build_ui()
        self._pm.profile_switched.connect(self._refresh)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        heading = QLabel("Zoom Behavior & Physics")
        heading.setObjectName("heading")
        outer.addWidget(heading)

        sub = QLabel("Configure how IceZoom magnifies the screen and responds to input.")
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Content placed directly — the outer QScrollArea is provided by MainWindow
        layout = outer
        layout.setSpacing(12)

        # ── Zoom Mode ─────────────────────────────────────────────────────────
        layout.addWidget(self._section("ZOOM MODE"))

        mode_card = self._card()
        mode_inner = QVBoxLayout(mode_card)
        mode_inner.setSpacing(10)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Behavior"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Follow Mouse", "Fixed Position"])
        self._mode_combo.setCurrentText(self._pm.get("zoom_behavior", "Follow Mouse"))
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_row.addStretch()
        mode_row.addWidget(self._mode_combo)
        mode_inner.addLayout(mode_row)

        # Fixed position coords (shown/hidden based on mode)
        self._coord_frame = QFrame()
        coord_layout = QHBoxLayout(self._coord_frame)
        coord_layout.setContentsMargins(0, 0, 0, 0)
        coord_layout.setSpacing(12)

        coord_layout.addWidget(QLabel("X"))
        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 7680)
        self._x_spin.setValue(self._pm.get("zoom_fixed_x", 960))
        self._x_spin.valueChanged.connect(lambda v: self._pm.set("zoom_fixed_x", v))
        coord_layout.addWidget(self._x_spin)

        coord_layout.addWidget(QLabel("Y"))
        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 4320)
        self._y_spin.setValue(self._pm.get("zoom_fixed_y", 540))
        self._y_spin.valueChanged.connect(lambda v: self._pm.set("zoom_fixed_y", v))
        coord_layout.addWidget(self._y_spin)
        coord_layout.addStretch()

        mode_inner.addWidget(self._coord_frame)
        self._update_coord_visibility()
        layout.addWidget(mode_card)

        # ── Zoom Factor ───────────────────────────────────────────────────────
        layout.addWidget(self._section("ZOOM FACTOR"))

        factor_card = self._card()
        factor_inner = QVBoxLayout(factor_card)
        factor_inner.setSpacing(10)

        # Zoom slider
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Zoom Level"))
        zoom_row.addStretch()
        self._zoom_val_lbl = QLabel(f"{self._pm.get('zoom_factor', 2.0):.1f}×")
        self._zoom_val_lbl.setObjectName("value_label")
        zoom_row.addWidget(self._zoom_val_lbl)
        factor_inner.addLayout(zoom_row)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(10, 100)
        self._zoom_slider.setValue(int(self._pm.get("zoom_factor", 2.0) * 10))
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider)
        factor_inner.addWidget(self._zoom_slider)

        # Min / Max
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Min"))
        self._min_spin = QDoubleSpinBox()
        self._min_spin.setRange(1.0, 5.0)
        self._min_spin.setSingleStep(0.1)
        self._min_spin.setValue(self._pm.get("zoom_min", 1.0))
        self._min_spin.valueChanged.connect(lambda v: self._pm.set("zoom_min", v))
        range_row.addWidget(self._min_spin)
        range_row.addStretch()
        range_row.addWidget(QLabel("Max"))
        self._max_spin = QDoubleSpinBox()
        self._max_spin.setRange(2.0, 10.0)
        self._max_spin.setSingleStep(0.5)
        self._max_spin.setValue(self._pm.get("zoom_max", 10.0))
        self._max_spin.valueChanged.connect(lambda v: self._pm.set("zoom_max", v))
        range_row.addWidget(self._max_spin)
        factor_inner.addLayout(range_row)

        # Zoom step
        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("Increment Step"))
        step_row.addStretch()
        self._step_spin = QDoubleSpinBox()
        self._step_spin.setRange(0.1, 2.0)
        self._step_spin.setSingleStep(0.1)
        self._step_spin.setValue(self._pm.get("zoom_step", 0.3))
        self._step_spin.valueChanged.connect(lambda v: self._pm.set("zoom_step", v))
        step_row.addWidget(self._step_spin)
        factor_inner.addLayout(step_row)

        layout.addWidget(factor_card)

        # ── Toggles ───────────────────────────────────────────────────────────
        layout.addWidget(self._section("BEHAVIOR TOGGLES"))

        toggle_card = self._card()
        toggle_inner = QVBoxLayout(toggle_card)
        toggle_inner.setSpacing(12)

        # Animations
        anim_row = QHBoxLayout()
        anim_row.addWidget(QLabel("Zoom Animations"))
        anim_desc = QLabel("Smooth transition when zooming in/out")
        anim_desc.setObjectName("muted")
        anim_row.addWidget(anim_desc)
        anim_row.addStretch()
        self._anim_toggle = ToggleSwitch(self._pm.get("zoom_animations", True))
        self._anim_toggle.toggled.connect(self._on_anim_toggle)
        anim_row.addWidget(self._anim_toggle)
        toggle_inner.addLayout(anim_row)

        sep = QFrame(); sep.setObjectName("separator"); toggle_inner.addWidget(sep)

        # Mouse sensitivity
        sens_row = QHBoxLayout()
        sens_row.addWidget(QLabel("Reduce Mouse Sensitivity"))
        sens_desc = QLabel("Scale down DPI while zoomed in")
        sens_desc.setObjectName("muted")
        sens_row.addWidget(sens_desc)
        sens_row.addStretch()
        self._sens_toggle = ToggleSwitch(self._pm.get("zoom_mouse_sensitivity", True))
        self._sens_toggle.toggled.connect(self._on_sens_toggle)
        sens_row.addWidget(self._sens_toggle)
        toggle_inner.addLayout(sens_row)

        sep2 = QFrame(); sep2.setObjectName("separator"); toggle_inner.addWidget(sep2)

        # PiP mode
        pip_row = QHBoxLayout()
        pip_row.addWidget(QLabel("Picture-in-Picture Mode"))
        pip_desc = QLabel("Dock zoom into a floating window")
        pip_desc.setObjectName("muted")
        pip_row.addWidget(pip_desc)
        pip_row.addStretch()
        self._pip_toggle = ToggleSwitch(self._pm.get("pip_mode", False))
        self._pip_toggle.toggled.connect(self._on_pip_toggle)
        pip_row.addWidget(self._pip_toggle)
        toggle_inner.addLayout(pip_row)

        layout.addWidget(toggle_card)
        layout.addStretch()

        # Sync zoom engine to profile changes
        self._ze.zoom_factor_changed.connect(self._on_engine_zoom_changed)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section_title")
        return lbl

    def _card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        return card

    def _update_coord_visibility(self):
        mode = self._pm.get("zoom_behavior", "Follow Mouse")
        self._coord_frame.setVisible(mode == "Fixed Position")

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_mode_changed(self, mode: str):
        self._pm.set("zoom_behavior", mode)
        self._update_coord_visibility()

    def _on_zoom_slider(self, value: int):
        factor = value / 10.0
        self._zoom_val_lbl.setText(f"{factor:.1f}×")
        self._pm.set("zoom_factor", factor)
        self._ze.set_zoom_factor(factor)

    def _on_engine_zoom_changed(self, factor: float):
        """Keep slider in sync when zoom changes via hotkey."""
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(int(factor * 10))
        self._zoom_val_lbl.setText(f"{factor:.1f}×")
        self._zoom_slider.blockSignals(False)

    def _on_pip_toggle(self, enabled: bool):
        self._pm.set("pip_mode", enabled)
        # Signal main window to switch display mode
        self.parent_window_pip_changed(enabled) if hasattr(self, "_pip_callback") else None

    def set_pip_callback(self, callback):
        self._pip_callback = callback
        self._pip_toggle.toggled.connect(callback)

    def _refresh(self, _name: str = ""):
        """Reload all controls from active profile."""
        self._mode_combo.blockSignals(True)
        self._mode_combo.setCurrentText(self._pm.get("zoom_behavior", "Follow Mouse"))
        self._mode_combo.blockSignals(False)
        self._update_coord_visibility()

        self._x_spin.blockSignals(True)
        self._x_spin.setValue(self._pm.get("zoom_fixed_x", 960))
        self._x_spin.blockSignals(False)

        self._y_spin.blockSignals(True)
        self._y_spin.setValue(self._pm.get("zoom_fixed_y", 540))
        self._y_spin.blockSignals(False)

        factor = self._pm.get("zoom_factor", 2.0)
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(int(factor * 10))
        self._zoom_val_lbl.setText(f"{factor:.1f}×")
        self._zoom_slider.blockSignals(False)

        self._step_spin.blockSignals(True)
        self._step_spin.setValue(self._pm.get("zoom_step", 0.3))
        self._step_spin.blockSignals(False)

        self._anim_toggle.setChecked(self._pm.get("zoom_animations", True))
        self._sens_toggle.setChecked(self._pm.get("zoom_mouse_sensitivity", True))
        self._pip_toggle.setChecked(self._pm.get("pip_mode", False))

    # ── Live-setting slots ───────────────────────────────────────────────────

    def _on_anim_toggle(self, enabled: bool):
        """Persist the setting and notify the engine so it takes effect immediately."""
        self._pm.set("zoom_animations", enabled)
        self._ze.on_animation_setting_changed(enabled)

    def _on_sens_toggle(self, enabled: bool):
        """Persist the setting and notify the engine so it takes effect immediately."""
        self._pm.set("zoom_mouse_sensitivity", enabled)
        self._ze.on_sensitivity_setting_changed(enabled)
