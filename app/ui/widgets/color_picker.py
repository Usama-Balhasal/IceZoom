"""
IceZoom — Color + Opacity Picker Widget
Combines a color swatch button (opens QColorDialog) with an opacity slider.
Emits color_changed(hex_str, opacity_float).
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QColorDialog
)


class ColorOpacityWidget(QWidget):
    """
    A compact color-picker + opacity slider combo.
    """
    color_changed = pyqtSignal(str, float)   # (hex_color, opacity 0-1)

    def __init__(self, color: str = "#FFFFFF", opacity: float = 1.0, parent=None):
        super().__init__(parent)
        self._color = color
        self._opacity = max(0.0, min(1.0, opacity))
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Color swatch button
        self._swatch = QPushButton()
        self._swatch.setFixedSize(34, 34)
        self._swatch.setToolTip("Click to change color")
        self._swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._swatch.clicked.connect(self._open_color_dialog)
        self._update_swatch()
        layout.addWidget(self._swatch)

        # Opacity slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(int(self._opacity * 100))
        self._slider.setFixedHeight(20)
        self._slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self._slider)

        # Opacity value label
        self._label = QLabel(f"{int(self._opacity * 100)}%")
        self._label.setObjectName("value_label")
        self._label.setFixedWidth(38)
        layout.addWidget(self._label)

    def _update_swatch(self):
        c = QColor(self._color)
        darker = c.darker(130).name()
        self._swatch.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid {darker};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border: 2px solid #00D4FF;
            }}
        """)

    def _open_color_dialog(self):
        initial = QColor(self._color)
        color = QColorDialog.getColor(
            initial, self, "Choose Color",
            QColorDialog.ColorDialogOption.DontUseNativeDialog
        )
        if color.isValid():
            self._color = color.name()
            self._update_swatch()
            self.color_changed.emit(self._color, self._opacity)

    def _on_opacity_changed(self, value: int):
        self._opacity = value / 100.0
        self._label.setText(f"{value}%")
        self.color_changed.emit(self._color, self._opacity)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_color(self) -> str:
        return self._color

    def get_opacity(self) -> float:
        return self._opacity

    def set_color(self, color: str):
        self._color = color
        self._update_swatch()

    def set_opacity(self, opacity: float):
        self._opacity = opacity
        self._slider.setValue(int(opacity * 100))
        self._label.setText(f"{int(opacity * 100)}%")
