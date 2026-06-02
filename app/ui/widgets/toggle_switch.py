"""
IceZoom — Animated Toggle Switch Widget
iOS-style ON/OFF toggle with smooth animation and ice-blue coloring.
"""
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtProperty,
    pyqtSignal, QRect, QRectF
)
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    """
    An animated toggle switch that emits toggled(bool) on state change.
    """
    toggled = pyqtSignal(bool)

    WIDTH  = 50
    HEIGHT = 26
    RADIUS = 13

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._checked = checked
        self._thumb_x = float(self.HEIGHT - 4 + (self.WIDTH - self.HEIGHT) * int(checked))

        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Property ──────────────────────────────────────────────────────────────

    def _get_thumb_x(self) -> float:
        return self._thumb_x

    def _set_thumb_x(self, v: float):
        self._thumb_x = v
        self.update()

    thumb_x = pyqtProperty(float, _get_thumb_x, _set_thumb_x)

    # ── Public API ────────────────────────────────────────────────────────────

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, emit: bool = False):
        if checked == self._checked:
            return
        self._checked = checked
        self._animate()
        if emit:
            self.toggled.emit(checked)

    def toggle(self):
        self.setChecked(not self._checked, emit=True)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _animate(self):
        thumb_r = self.HEIGHT - 4
        start = self._thumb_x
        end = self._target_x()
        self._anim.setStartValue(start)
        self._anim.setEndValue(float(end))
        self._anim.start()

    def _target_x(self) -> float:
        """Compute the correct resting X for the thumb centre in the current state."""
        thumb_r = self.HEIGHT - 4
        if not self._checked:
            return float(thumb_r // 2 + 2)
        else:
            return float(self.WIDTH - thumb_r // 2 - 2)

    def _snap_to_state(self):
        """Immediately position the thumb without animation (used on first show)."""
        self._thumb_x = self._target_x()
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.WIDTH, self.HEIGHT
        r = h / 2

        # Track
        if self._checked:
            # Gradient-ish ice blue
            track_color = QColor("#007F99")
        else:
            track_color = QColor("#30363D")

        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Active fill overlay (shows progress)
        if self._checked:
            ice = QColor("#00D4FF")
            ice.setAlpha(180)
            painter.setBrush(QBrush(ice))
            painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Thumb
        thumb_d = h - 6
        thumb_y = 3
        thumb_x = self._thumb_x - thumb_d / 2
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(thumb_x, thumb_y, thumb_d, thumb_d))

        painter.end()

    def showEvent(self, event):
        """Snap thumb to the correct resting position once geometry is finalised."""
        super().showEvent(event)
        self._snap_to_state()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
