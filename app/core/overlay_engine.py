"""
IceZoom — Overlay Engine
A transparent, always-on-top, full-screen overlay window that:
  - Dims/blurs the area outside the focus shape
  - Draws a shaped cutout (Circle or Square) showing the zoomed content
  - Optionally draws an outline ring and crosshair
  - Is completely transparent to mouse events
"""
import ctypes
import sys
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, pyqtSlot
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QPixmap, QFont, QRadialGradient
)
from PyQt6.QtWidgets import QWidget, QApplication

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


class OverlayEngine(QWidget):
    """
    Full-screen transparent overlay with a shaped cutout + zoom content.
    """

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._pixmap: QPixmap | None = None
        self._center_x = 960
        self._center_y = 540
        self._visible = False
        self._eyedropper_color: str | None = None

        self._setup_window()

    def _setup_window(self):
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def showEvent(self, event):
        """Apply capture exclusion once the native window handle exists."""
        super().showEvent(event)
        _apply_capture_exclusion(int(self.winId()))

    # ── Public Control ────────────────────────────────────────────────────────

    def set_visible(self, visible: bool):
        self._visible = visible
        if visible:
            self.show()
            self.raise_()
        else:
            self.hide()

    @pyqtSlot(QPixmap, int, int)
    def update_frame(self, pixmap: QPixmap, cx: int, cy: int):
        self._pixmap = pixmap
        self._center_x = cx
        self._center_y = cy
        if self._visible:
            self.update()

    def set_eyedropper_color(self, color: str):
        self._eyedropper_color = color
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if not self._visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        screen_rect = self.rect()
        focus_enabled = self._pm.get("focus_enabled", True)
        shape = self._pm.get("focus_shape", "Circle")
        size = self._pm.get("focus_size", 300)
        half = size // 2

        cx, cy = self._center_x, self._center_y

        # Build focus shape path
        shape_path = QPainterPath()
        if shape == "Circle":
            shape_path.addEllipse(QRectF(cx - half, cy - half, size, size))
        else:
            shape_path.addRoundedRect(QRectF(cx - half, cy - half, size, size), 12, 12)

        # ── 1. Draw zoomed pixmap inside the shape ────────────────────────────
        if self._pixmap:
            painter.save()
            painter.setClipPath(shape_path)
            dest = QRectF(cx - half, cy - half, size, size)
            painter.drawPixmap(dest.toRect(), self._pixmap)
            painter.restore()

        # ── 2. Background dim outside the shape ───────────────────────────────
        if focus_enabled and self._pm.get("focus_bg_enabled", True):
            bg_color = QColor(self._pm.get("focus_bg_color", "#000000"))
            bg_opacity = self._pm.get("focus_bg_opacity", 0.55)
            bg_color.setAlphaF(bg_opacity)

            full_path = QPainterPath()
            full_path.addRect(QRectF(screen_rect))
            outside = full_path.subtracted(shape_path)

            painter.fillPath(outside, QBrush(bg_color))

        # ── 3. Outline ring ───────────────────────────────────────────────────
        if focus_enabled and self._pm.get("focus_outline_enabled", True):
            outline_color = QColor(self._pm.get("focus_outline_color", "#00D4FF"))
            outline_opacity = self._pm.get("focus_outline_opacity", 1.0)
            outline_color.setAlphaF(outline_opacity)
            outline_w = self._pm.get("focus_outline_width", 3)

            pen = QPen(outline_color, outline_w)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(shape_path)

        # ── 4. Crosshair ──────────────────────────────────────────────────────
        if focus_enabled and self._pm.get("crosshair_enabled", False):
            ch_color = QColor(self._pm.get("crosshair_color", "#FF4444"))
            ch_opacity = self._pm.get("crosshair_opacity", 0.9)
            ch_color.setAlphaF(ch_opacity)
            ch_size = self._pm.get("crosshair_size", 20)
            ch_thick = self._pm.get("crosshair_thickness", 2)

            ch_pen = QPen(ch_color, ch_thick)
            ch_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(ch_pen)

            # Horizontal bar
            painter.drawLine(
                int(cx - ch_size), cy,
                int(cx + ch_size), cy
            )
            # Vertical bar
            painter.drawLine(
                cx, int(cy - ch_size),
                cx, int(cy + ch_size)
            )
            # Center dot
            painter.setBrush(QBrush(ch_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy), ch_thick + 1, ch_thick + 1)

        # ── 5. Eyedropper color badge ─────────────────────────────────────────
        if self._eyedropper_color:
            swatch_size = 60
            swatch_x = cx + half + 12
            swatch_y = cy - swatch_size // 2

            painter.setBrush(QBrush(QColor(self._eyedropper_color)))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawRoundedRect(swatch_x, swatch_y, swatch_size, swatch_size // 2, 4, 4)

            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                swatch_x, swatch_y + swatch_size // 2 + 18,
                self._eyedropper_color
            )

        painter.end()
