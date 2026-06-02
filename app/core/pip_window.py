"""
IceZoom — Picture-in-Picture Window
A draggable, resizable, always-on-top borderless window that displays
the zoomed view without covering the whole screen.
"""
import ctypes
import sys
from PyQt6.QtCore import Qt, QPoint, QSize, QRect, QRectF, pyqtSlot
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QPixmap,
    QLinearGradient, QCursor
)
from PyQt6.QtWidgets import QWidget, QSizeGrip, QApplication
from app.utils.constants import BG_DARK, BG_PANEL, ICE_BLUE, TEXT_MUTED

# Windows constant: exclude this window from all screen capture / BitBlt sources
_WDA_EXCLUDEFROMCAPTURE = 0x00000011


def _apply_capture_exclusion(hwnd: int) -> None:
    """Make the window invisible to mss / BitBlt screen capture (Windows only)."""
    if sys.platform != "win32" or not hwnd:
        return
    try:
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, _WDA_EXCLUDEFROMCAPTURE)
    except Exception:
        pass


class PiPWindow(QWidget):
    """
    A floating Picture-in-Picture window for the magnified view.
    Features: drag to move, corner grip to resize, rounded corners, glass border.
    """

    HEADER_H = 28
    CORNER_RADIUS = 10

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._pixmap: QPixmap | None = None
        self._drag_start: QPoint | None = None
        self._dragging = False

        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(160, 120)

        # Restore saved position/size from profile
        x = self._pm.get("pip_x", 100)
        y = self._pm.get("pip_y", 100)
        w = self._pm.get("pip_width", 400)
        h = self._pm.get("pip_height", 300)
        self.setGeometry(x, y, w, h)

        # Resize grip
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(16, 16)
        self._grip.setStyleSheet("background: transparent;")

    def showEvent(self, event):
        """Apply capture exclusion once the native window handle exists."""
        super().showEvent(event)
        _apply_capture_exclusion(int(self.winId()))

    # ── Frame Update ──────────────────────────────────────────────────────────

    @pyqtSlot(QPixmap, int, int)
    def update_frame(self, pixmap: QPixmap, cx: int, cy: int):
        self._pixmap = pixmap
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        r = self.CORNER_RADIUS

        # Content area (below header)
        content_rect = QRectF(0, self.HEADER_H, w, h - self.HEADER_H)

        # ── Background ────────────────────────────────────────────────────────
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), r, r)
        painter.setClipPath(clip)

        # Background fill
        painter.fillRect(0, 0, w, h, QColor(BG_DARK))

        # ── Header bar ──────────────────────────────────────────────────────────────
        header_grad = QLinearGradient(0, 0, 0, self.HEADER_H)
        header_grad.setColorAt(0, QColor(BG_PANEL))
        header_grad.setColorAt(1, QColor(BG_DARK))
        painter.fillRect(0, 0, w, self.HEADER_H, QBrush(header_grad))

        # Header text
        painter.setPen(QColor(ICE_BLUE))
        from PyQt6.QtGui import QFont
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(10, 2, w - 40, self.HEADER_H - 2,
                         Qt.AlignmentFlag.AlignVCenter, "❄  IceZoom PiP")

        # ── Zoom content ──────────────────────────────────────────────────────
        if self._pixmap:
            painter.setClipRect(content_rect.toRect())
            painter.drawPixmap(content_rect.toRect(), self._pixmap)
            painter.setClipping(False)
        else:
            # Placeholder when not active
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(content_rect.toRect(),
                             Qt.AlignmentFlag.AlignCenter, "Zoom not active")

        # Outline border
        painter.setClipping(False)
        border_pen = QPen(QColor(ICE_BLUE), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        border_path = QPainterPath()
        border_path.addRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), r, r)
        painter.drawPath(border_path)

        painter.end()

    def resizeEvent(self, event):
        self._grip.move(self.width() - self._grip.width(),
                        self.height() - self._grip.height())
        self._save_geometry()

    def moveEvent(self, event):
        self._save_geometry()

    def _save_geometry(self):
        self._pm.set("pip_x", self.x())
        self._pm.set("pip_y", self.y())
        self._pm.set("pip_width", self.width())
        self._pm.set("pip_height", self.height())

    # ── Dragging ──────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() < self.HEADER_H:
                self._dragging = True
                self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start:
            self.move(event.globalPosition().toPoint() - self._drag_start)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_start = None

    def mouseDoubleClickEvent(self, event):
        """Double-click header to reset size."""
        if event.position().y() < self.HEADER_H:
            self.resize(400, 300)
