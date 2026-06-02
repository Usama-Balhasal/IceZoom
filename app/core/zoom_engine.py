"""
IceZoom — Zoom Engine
Captures a screen region using mss and emits scaled QPixmaps for the
overlay and PiP windows. Runs on a QTimer at ~60fps.
"""
import ctypes
from typing import Optional, Tuple

import mss
import mss.tools
from PIL import Image

from PyQt6.QtCore import (
    QObject, QTimer, pyqtSignal, QPoint, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QRect
)
from PyQt6.QtGui import QPixmap, QImage, QCursor
from PyQt6.QtWidgets import QApplication

from app.utils.constants import CAPTURE_BASE_SIZE, OVERLAY_FPS


class ZoomEngine(QObject):
    """
    Captures a region of the screen and emits a scaled QPixmap.

    Signals
    -------
    frame_ready(pixmap, center_x, center_y)
    zoom_factor_changed(factor)
    """

    frame_ready          = pyqtSignal(QPixmap, int, int)
    zoom_factor_changed  = pyqtSignal(float)
    eyedropper_color     = pyqtSignal(str)   # hex color when frozen

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._active = False
        self._hold_active = False
        self._frozen = False
        self._frozen_pixmap: Optional[QPixmap] = None

        # Animated zoom factor
        self._display_factor: float = 1.0
        self._target_factor: float = 2.0

        self._timer = QTimer(self)
        self._timer.setInterval(1000 // OVERLAY_FPS)
        self._timer.timeout.connect(self._tick)

        self._sct = mss.mss()
        self._last_center = (0, 0)

    # ── PyQt property for smooth animation ──────────────────────────────────

    def _get_display_factor(self) -> float:
        return self._display_factor

    def _set_display_factor(self, v: float):
        self._display_factor = max(1.0, v)

    displayFactor = pyqtProperty(float, _get_display_factor, _set_display_factor)

    # ── Control ──────────────────────────────────────────────────────────────

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._target_factor = self._pm.get("zoom_factor", 2.0)
            self._start_anim()
            self._timer.start()
        else:
            self._stop_anim()
            self._timer.stop()

    def set_hold_active(self, active: bool):
        self._hold_active = active
        self.set_active(active)

    def is_active(self) -> bool:
        return self._active

    def increase_zoom(self):
        step  = self._pm.get("zoom_step", 0.3)
        max_z = self._pm.get("zoom_max", 10.0)
        # If currently at the baseline (1.0×), snap cleanly to the first
        # meaningful zoom level rather than incrementing from 1.0 in tiny steps.
        _MIN_MEANINGFUL = 1.3
        if self._target_factor <= 1.0:
            new_factor = min(_MIN_MEANINGFUL, max_z)
        else:
            new_factor = min(self._target_factor + step, max_z)
        self._pm.set("zoom_factor", new_factor)
        self._target_factor = new_factor
        self._start_anim()
        self.zoom_factor_changed.emit(new_factor)

    def decrease_zoom(self):
        step = self._pm.get("zoom_step", 0.3)
        min_z = self._pm.get("zoom_min", 1.0)
        new_factor = max(self._target_factor - step, min_z)
        self._pm.set("zoom_factor", new_factor)
        self._target_factor = new_factor
        self._start_anim()
        self.zoom_factor_changed.emit(new_factor)

    def reset_zoom(self):
        default = 2.0
        self._pm.set("zoom_factor", default)
        self._target_factor = default
        self._start_anim()
        self.zoom_factor_changed.emit(default)

    def set_zoom_factor(self, factor: float):
        self._target_factor = factor
        self._start_anim()
        self.zoom_factor_changed.emit(factor)

    def toggle_freeze(self):
        """Toggle eyedropper freeze mode."""
        self._frozen = not self._frozen
        if not self._frozen:
            self._frozen_pixmap = None

    # ── Live-setting callbacks ───────────────────────────────────────────────────

    def on_animation_setting_changed(self, enabled: bool):
        """
        Called immediately when the 'Zoom Animations' toggle changes.
        If animations are disabled while zoom is active, snap the display
        factor to the target immediately rather than leaving a stale animation.
        """
        if not enabled and self._active:
            self._stop_anim()
            self._display_factor = self._target_factor

    def on_sensitivity_setting_changed(self, enabled: bool):
        """
        Called immediately when the 'Reduce Mouse Sensitivity' toggle changes.
        Re-applies (or restores) mouse speed if zoom is currently running.
        """
        if self._active or self._hold_active:
            # apply_mouse_sensitivity reads the flag from profile_manager itself;
            # we just need to call it with the correct active state.
            self.apply_mouse_sensitivity(True)
        else:
            # Zoom is not active; ensure speed is restored regardless.
            self.apply_mouse_sensitivity(False)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _start_anim(self):
        if self._pm.get("zoom_animations", True):
            if hasattr(self, "_anim") and self._anim.state() == QPropertyAnimation.State.Running:
                self._anim.stop()
            self._anim = QPropertyAnimation(self, b"displayFactor", self)
            self._anim.setDuration(180)
            self._anim.setStartValue(self._display_factor)
            self._anim.setEndValue(self._target_factor)
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.start()
        else:
            self._display_factor = self._target_factor

    def _stop_anim(self):
        if hasattr(self, "_anim"):
            self._anim.stop()

    # ── Capture Loop ──────────────────────────────────────────────────────────

    def _tick(self):
        if not self._active:
            return

        factor = self._display_factor

        # ── Baseline bypass (1.0×) ────────────────────────────────────────────
        # At exactly 1.0× there is no magnification: skip all capture/crop/scale
        # math entirely.  Grab the full screen region at native resolution and
        # display it directly — zero wasted computation.
        if factor <= 1.0:
            behavior = self._pm.get("zoom_behavior", "Follow Mouse")
            if behavior == "Follow Mouse":
                cursor = QCursor.pos()
                cx, cy = cursor.x(), cursor.y()
            else:
                cx = self._pm.get("zoom_fixed_x", 960)
                cy = self._pm.get("zoom_fixed_y", 540)
            self._last_center = (cx, cy)

            screen = QApplication.primaryScreen().geometry()
            cap = CAPTURE_BASE_SIZE
            half = cap // 2
            x1 = max(0, min(cx - half, screen.width()  - cap))
            y1 = max(0, min(cy - half, screen.height() - cap))

            try:
                mon = {"left": x1, "top": y1, "width": cap, "height": cap}
                shot = self._sct.grab(mon)
                img = Image.frombytes("RGB", shot.size, shot.rgb)
                # No resize — 1:1 passthrough
                qimg = QImage(
                    img.tobytes(), img.width, img.height,
                    img.width * 3, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qimg)
                self.frame_ready.emit(pixmap, cx, cy)
            except Exception:
                pass
            return

        # ── Normal magnified capture ──────────────────────────────────────────
        behavior = self._pm.get("zoom_behavior", "Follow Mouse")
        if behavior == "Follow Mouse":
            cursor = QCursor.pos()
            cx, cy = cursor.x(), cursor.y()
        else:
            cx = self._pm.get("zoom_fixed_x", 960)
            cy = self._pm.get("zoom_fixed_y", 540)

        self._last_center = (cx, cy)
        cap_size = int(CAPTURE_BASE_SIZE / factor)
        half = cap_size // 2

        # Clamp to screen bounds
        screen = QApplication.primaryScreen().geometry()
        x1 = max(0, cx - half)
        y1 = max(0, cy - half)
        x2 = min(screen.width(),  x1 + cap_size)
        y2 = min(screen.height(), y1 + cap_size)
        x1 = max(0, x2 - cap_size)
        y1 = max(0, y2 - cap_size)

        if self._frozen and self._frozen_pixmap:
            self.frame_ready.emit(self._frozen_pixmap, cx, cy)
            # emit eyedropper color
            img = self._frozen_pixmap.toImage()
            px = img.pixel(img.width() // 2, img.height() // 2)
            from PyQt6.QtGui import QColor
            c = QColor(px)
            self.eyedropper_color.emit(c.name().upper())
            return

        try:
            mon = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
            shot = self._sct.grab(mon)
            img = Image.frombytes("RGB", shot.size, shot.rgb)

            # Scale up
            out_size = CAPTURE_BASE_SIZE
            img = img.resize((out_size, out_size), Image.LANCZOS)

            qimg = QImage(
                img.tobytes(), img.width, img.height,
                img.width * 3, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimg)

            if self._frozen:
                self._frozen_pixmap = pixmap

            self.frame_ready.emit(pixmap, cx, cy)

        except Exception:
            pass  # Screen capture can fail on edge cases; silently continue

    # ── Mouse Sensitivity ─────────────────────────────────────────────────────

    def apply_mouse_sensitivity(self, active: bool):
        """
        Scale mouse speed down while zoomed in (Windows only).
        Uses SystemParametersInfo to adjust mouse speed.
        """
        if not self._pm.get("zoom_mouse_sensitivity", True):
            return
        try:
            SPI_SETMOUSESPEED = 0x0071
            SPI_GETMOUSESPEED = 0x0070
            SPIF_SENDCHANGE = 0x0002

            speed = ctypes.c_int()
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0
            )
            if active:
                # Store original and set halved
                self._original_mouse_speed = speed.value
                new_speed = max(1, speed.value // 2)
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETMOUSESPEED, 0, new_speed, SPIF_SENDCHANGE
                )
            else:
                original = getattr(self, "_original_mouse_speed", speed.value)
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETMOUSESPEED, 0, original, SPIF_SENDCHANGE
                )
        except Exception:
            pass

    def cleanup(self):
        self._timer.stop()
        self.apply_mouse_sensitivity(False)
        try:
            self._sct.close()
        except Exception:
            pass
