"""
IceZoom — Hotkey Recorder Widget
Click to enter recording mode, press any key combination, widget captures it.
Supports keyboard keys AND mouse buttons / scroll wheel.
Validates for conflicts and displays the combo in a styled badge.

Supported mouse tokens (displayed title-cased in the badge):
  Mouse_LMB, Mouse_RMB, Mouse_MMB, Mouse_Scroll_Up, Mouse_Scroll_Down
"""
import keyboard
import mouse
from typing import Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)

# Mouse button → canonical token string
_MOUSE_BTN_TOKENS = {
    "left":   "Mouse_LMB",
    "right":  "Mouse_RMB",
    "middle": "Mouse_MMB",
}
_SCROLL_UP_TOKEN   = "Mouse_Scroll_Up"
_SCROLL_DOWN_TOKEN = "Mouse_Scroll_Down"

# Keys that are modifier-only and should not finalise the combo on their own.
# Includes localised names so a Danish/German/French layout doesn't trigger
# a premature finalise on modifier-key-down alone.
_MOD_KEYS = {
    "shift", "ctrl", "alt", "windows",
    "ctrl_r", "shift_r", "alt_r",
    "left shift", "right shift",
    "left ctrl", "right ctrl",
    "left alt", "right alt",
    # Localised equivalents
    "skift", "venstre skift", "højre skift",   # Danish
    "strg", "venstre ctrl", "højre ctrl",       # Danish ctrl
    "venstre alt", "højre alt",                 # Danish alt
    "umschalt",                                  # German
    "maj",                                       # French
}

# ── Locale → canonical English modifier map ───────────────────────────────────
# Covers common localised strings emitted by the `keyboard` library on
# non-English Windows keyboard layouts (e.g. Danish gives "Skift").
_LOCALE_MAP: dict[str, str] = {
    # lower-cased source → canonical display form
    "skift":         "Shift",
    "venstre skift": "Shift",
    "højre skift":   "Shift",
    "strg":          "Ctrl",
    "venstre ctrl":  "Ctrl",
    "højre ctrl":    "Ctrl",
    "venstre alt":   "Alt",
    "højre alt":     "Alt",
    "umschalt":      "Shift",   # German
    "maj":           "Shift",   # French
}


def _sanitise_key_name(name: str) -> str:
    """
    Convert a raw key name (as returned by the `keyboard` library) to a
    clean, standardised English display string.  Handles:
      • Localised modifier names  ("Skift" → "Shift", "Strg" → "Ctrl" …)
      • Left/right side variants  ("left shift" → "Shift")
      • Title-casing everything else
    """
    canonical = _LOCALE_MAP.get(name.lower())
    if canonical:
        return canonical
    # Strip directional prefix and title-case
    cleaned = (
        name
        .replace("left ",  "")
        .replace("right ", "")
        .replace("_r",     "")
    )
    return cleaned.title()


class HotkeyWidget(QWidget):
    """
    Displays the current hotkey combo and allows click-to-record.
    Emits combo_changed(action_id, new_combo) when a new binding is captured.
    """
    combo_changed = pyqtSignal(str, str)

    def __init__(self, action_id: str, combo: str = "", parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self._combo = combo
        self._recording = False
        self._pressed_keys: Set[str] = set()    # accumulates keys during recording
        self._kb_hook = None
        self._mouse_hook = None
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.setInterval(5000)
        self._timeout_timer.timeout.connect(self._stop_recording)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Combo display badge
        self._badge = QPushButton(self._format_combo(self._combo))
        self._badge.setObjectName("hotkey_badge")
        self._badge.setFixedHeight(34)
        self._badge.setMinimumWidth(160)
        self._badge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self._badge.clicked.connect(self._start_recording)
        self._badge.setStyleSheet(self._badge_style(False))
        layout.addWidget(self._badge)

        # Clear button
        self._clear_btn = QPushButton("✕")
        self._clear_btn.setObjectName("icon_btn")
        self._clear_btn.setFixedSize(28, 28)
        self._clear_btn.setToolTip("Clear hotkey")
        self._clear_btn.clicked.connect(self._clear)
        layout.addWidget(self._clear_btn)

    def _badge_style(self, recording: bool) -> str:
        if recording:
            return """
                QPushButton {
                    background: #1A3040;
                    border: 2px solid #00D4FF;
                    border-radius: 6px;
                    color: #00D4FF;
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 4px 12px;
                }
            """
        return """
            QPushButton {
                background: #161b22;
                border: 1px solid #30363D;
                border-radius: 6px;
                color: #E6EDF3;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
                text-align: center;
            }
            QPushButton:hover {
                border-color: #00D4FF;
                color: #00D4FF;
            }
        """

    def _format_combo(self, combo: str) -> str:
        if not combo:
            return "Click to set…"
        parts = [_sanitise_key_name(p.strip()) for p in combo.split("+")]
        return "  +  ".join(parts)

    # ── Recording ─────────────────────────────────────────────────────────────

    def _start_recording(self):
        if self._recording:
            self._stop_recording()
            return
        self._recording = True
        self._pressed_keys.clear()
        self._badge.setText("⬤  Press keys…")
        self._badge.setStyleSheet(self._badge_style(True))
        self._timeout_timer.start()

        # Hook keyboard
        try:
            self._kb_hook = keyboard.hook(self._on_key_event, suppress=False)
        except Exception:
            self._stop_recording()
            return

        # Hook mouse (buttons + scroll)
        try:
            self._mouse_hook = mouse.hook(self._on_mouse_event)
        except Exception:
            pass  # mouse support optional

    def _stop_recording(self):
        self._recording = False
        self._timeout_timer.stop()

        # Unhook keyboard
        if self._kb_hook is not None:
            try:
                keyboard.unhook(self._kb_hook)
            except Exception:
                pass
            self._kb_hook = None

        # Unhook mouse
        if self._mouse_hook is not None:
            try:
                mouse.unhook(self._mouse_hook)
            except Exception:
                pass
            self._mouse_hook = None

        self._badge.setStyleSheet(self._badge_style(False))
        self._badge.setText(self._format_combo(self._combo))

    # ── Key event handler ─────────────────────────────────────────────────────

    def _on_key_event(self, event):
        if not self._recording:
            return

        if event.event_type == keyboard.KEY_DOWN:
            name = event.name.lower() if event.name else ""
            if name and name not in ("unknown", ""):
                # Normalise right-side modifier variants
                name = name.replace("_r", "").replace("left ", "").replace("right ", "")
                self._pressed_keys.add(name)
                # Update badge live
                self._badge.setText(self._build_preview())

        elif event.event_type == keyboard.KEY_UP:
            # On any key release: if we have a non-modifier key in the set, finalise
            non_mods = [k for k in self._pressed_keys if k not in _MOD_KEYS
                        and not k.startswith("mouse_")]
            mouse_tokens = [k for k in self._pressed_keys if k.startswith("Mouse_")
                            or k.startswith("mouse_")]
            if non_mods or mouse_tokens:
                self._finalise()

    # ── Mouse event handler ───────────────────────────────────────────────────

    def _on_mouse_event(self, event):
        if not self._recording:
            return

        if isinstance(event, mouse.ButtonEvent):
            token = _MOUSE_BTN_TOKENS.get(event.button)
            if token is None:
                return

            if event.event_type == mouse.DOWN:
                self._pressed_keys.add(token)
                self._badge.setText(self._build_preview())
            elif event.event_type == mouse.UP:
                # Finalise on button release (same as key-up logic)
                self._pressed_keys.add(token)  # ensure it's counted
                self._finalise()

        elif isinstance(event, mouse.WheelEvent):
            token = _SCROLL_UP_TOKEN if event.delta > 0 else _SCROLL_DOWN_TOKEN
            self._pressed_keys.add(token)
            # Scroll has no "up" event — finalise immediately
            self._finalise()

    # ── Combo building ────────────────────────────────────────────────────────

    def _build_preview(self) -> str:
        """Build a human-readable preview of pressed keys so far."""
        mods, normal, mouse_toks = self._classify_keys()
        parts = sorted(mods) + normal + mouse_toks
        if not parts:
            return "⬤  Press keys…"
        return "  +  ".join(_sanitise_key_name(p) for p in parts)

    def _classify_keys(self):
        """Split _pressed_keys into (modifier_list, normal_list, mouse_token_list)."""
        mods, normal, mouse_toks = [], [], []
        for k in self._pressed_keys:
            lk = k.lower()
            if lk in _MOD_KEYS:
                # Normalise modifier display name
                clean = lk.replace("_r", "").replace("ctrl", "ctrl")
                if clean not in mods:
                    mods.append(clean)
            elif lk.startswith("mouse_"):
                mouse_toks.append(k)   # preserve original casing (Mouse_RMB etc.)
            else:
                normal.append(k)
        return mods, normal, mouse_toks

    def _finalise(self):
        """
        Build the final combo string and emit, then stop recording.
        Keys are stored in their sanitised (canonical English) form so
        backend comparison strings never contain localised modifier names.
        """
        mods, normal, mouse_toks = self._classify_keys()
        parts = sorted(mods) + normal + mouse_toks
        if parts:
            # Sanitise each part before joining to ensure "Shift" not "Skift"
            sanitised = [_sanitise_key_name(p).lower() for p in parts]
            # Preserve Mouse_* token casing
            final_parts = []
            for orig, san in zip(parts, sanitised):
                if orig.lower().startswith("mouse_"):
                    final_parts.append(orig)   # keep Mouse_RMB casing
                else:
                    final_parts.append(san)
            combo = "+".join(final_parts)
            self._combo = combo
            self.combo_changed.emit(self.action_id, combo)
        self._stop_recording()

    def _clear(self):
        self._combo = ""
        self._badge.setText(self._format_combo(""))
        self.combo_changed.emit(self.action_id, "")

    # ── Public ────────────────────────────────────────────────────────────────

    def get_combo(self) -> str:
        return self._combo

    def set_combo(self, combo: str):
        self._combo = combo
        self._badge.setText(self._format_combo(combo))
