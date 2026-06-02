"""
IceZoom — Application Entry Point
Bootstraps all core modules, wires signals, and starts the Qt event loop.
"""
import sys
import os

# ── Ensure project root is on Python path ─────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QCoreApplication

from app.utils.constants import (
    APP_NAME, APP_VERSION, ORG_NAME,
    BG_DARK, ICE_BLUE,
)
from app.utils.theme import apply_theme, safe_font_size

from app.core.profile_manager import ProfileManager
from app.core.hotkey_manager  import HotkeyManager
from app.core.zoom_engine     import ZoomEngine
from app.core.overlay_engine  import OverlayEngine
from app.core.pip_window      import PiPWindow
from app.core.auto_switcher   import AutoSwitcher

from app.ui.main_window import MainWindow
from app.ui.tray_icon   import TrayIcon


def _load_icon() -> QIcon:
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    # Fallback: generate a simple pixmap icon
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
    px = QPixmap(64, 64)
    px.fill(QColor(BG_DARK))
    p = QPainter(px)
    p.setBrush(QBrush(QColor(ICE_BLUE)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(12, 12, 40, 40)
    p.end()
    return QIcon(px)


def main():
    # ── Qt Application Setup ──────────────────────────────────────────────────
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)   # stay alive in tray

    # ── Font ──────────────────────────────────────────────────────────────────
    _base_size = safe_font_size(10)   # guard: never <= 0
    font = QFont("Segoe UI", _base_size)
    app.setFont(font)

    # ── Theme ─────────────────────────────────────────────────────────────────
    apply_theme(app)

    # ── Core Modules ──────────────────────────────────────────────────────────
    profile_manager = ProfileManager()
    hotkey_manager  = HotkeyManager()
    zoom_engine     = ZoomEngine(profile_manager)
    overlay_engine  = OverlayEngine(profile_manager)
    pip_window      = PiPWindow(profile_manager)

    # Load initial hotkey bindings from the active profile
    hotkey_manager.load_bindings(profile_manager.get("hotkeys", {}))

    # ── Main Window ───────────────────────────────────────────────────────────
    icon = _load_icon()
    main_window = MainWindow(
        profile_manager, hotkey_manager, zoom_engine,
        overlay_engine, pip_window
    )
    main_window.setWindowIcon(icon)

    # ── System Tray ───────────────────────────────────────────────────────────
    tray = TrayIcon(icon, profile_manager)
    tray.show()

    # Wire tray signals → main window / profile manager
    tray.show_settings.connect(main_window.show)
    tray.show_settings.connect(main_window.raise_)
    tray.show_settings.connect(main_window.activateWindow)
    tray.quit_requested.connect(_on_quit(app, zoom_engine, hotkey_manager))
    tray.profile_selected.connect(profile_manager.switch)
    tray.toggle_requested.connect(_make_tray_toggle(main_window))

    # ── Zoom Engine → Overlay / PiP routing ──────────────────────────────────
    def route_frame(pixmap, cx, cy):
        if profile_manager.get("pip_mode", False):
            pip_window.update_frame(pixmap, cx, cy)
        else:
            overlay_engine.update_frame(pixmap, cx, cy)

    zoom_engine.frame_ready.connect(route_frame)
    zoom_engine.eyedropper_color.connect(overlay_engine.set_eyedropper_color)

    # ── Hotkey Actions ────────────────────────────────────────────────────────
    def on_action(action_id: str):
        if action_id == "global_toggle":
            current = main_window._zoom_active
            new_state = not current
            main_window.set_global_toggle_state(new_state)
            main_window._on_global_toggle(new_state)
            main_window._global_toggle.setChecked(new_state, emit=False)
            tray.set_enabled_state(new_state)

        elif action_id == "increase_zoom":
            zoom_engine.increase_zoom()

        elif action_id == "decrease_zoom":
            zoom_engine.decrease_zoom()

        elif action_id == "reset_zoom":
            zoom_engine.reset_zoom()

        elif action_id == "quit_app":
            auto_switcher.stop()
            zoom_engine.cleanup()
            hotkey_manager.cleanup()
            app.quit()

    hotkey_manager.action_triggered.connect(on_action)

    def on_hold_start(action_id: str):
        if action_id == "toggle_zoom_hold" and not main_window._zoom_active:
            zoom_engine.set_hold_active(True)
            overlay_engine.set_visible(True)
            zoom_engine.apply_mouse_sensitivity(True)

    def on_hold_end(action_id: str):
        if action_id == "toggle_zoom_hold":
            zoom_engine.set_hold_active(False)
            if not main_window._zoom_active:
                overlay_engine.set_visible(False)
            zoom_engine.apply_mouse_sensitivity(False)

    hotkey_manager.action_held_start.connect(on_hold_start)
    hotkey_manager.action_held_end.connect(on_hold_end)

    # ── Profile Switch → Hotkey reload ───────────────────────────────────────
    def on_profile_switched(name: str):
        hotkey_manager.load_bindings(profile_manager.get("hotkeys", {}))

    profile_manager.profile_switched.connect(on_profile_switched)

    # ── Auto-Switcher ─────────────────────────────────────────────────────────
    auto_switcher = AutoSwitcher(profile_manager)
    auto_switcher.switch_to_profile.connect(profile_manager.switch)
    auto_switcher.start()

    # ── Show Main Window ──────────────────────────────────────────────────────
    main_window.show()

    # ── Tray notification ─────────────────────────────────────────────────────
    tray.showMessage(
        "IceZoom",
        f"Running in system tray. Active profile: {profile_manager.active_name()}",
        QIcon(icon),
        3000
    )

    # ── Run ───────────────────────────────────────────────────────────────────
    exit_code = app.exec()

    # Cleanup
    auto_switcher.stop()
    zoom_engine.cleanup()
    hotkey_manager.cleanup()

    sys.exit(exit_code)


def _on_quit(app, zoom_engine, hotkey_manager):
    def handler():
        zoom_engine.cleanup()
        hotkey_manager.cleanup()
        app.quit()
    return handler


def _make_tray_toggle(main_window):
    def handler():
        current = main_window._zoom_active
        new_state = not current
        main_window.set_global_toggle_state(new_state)
        main_window._on_global_toggle(new_state)
        main_window._global_toggle.setChecked(new_state, emit=False)
    return handler


if __name__ == "__main__":
    main()
