"""
IceZoom — Main Settings Window
Hosts the sidebar navigation and stacked settings panels.
"""
import winreg
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QColor, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QSizePolicy, QStatusBar, QSpacerItem
)

from app.ui.panels.profile_panel import ProfilePanel
from app.ui.panels.hotkey_panel import HotkeyPanel
from app.ui.panels.zoom_panel import ZoomPanel
from app.ui.panels.focus_panel import FocusPanel
from app.ui.widgets.toggle_switch import ToggleSwitch
from app.utils.constants import (
    APP_NAME, APP_VERSION,
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, SIDEBAR_WIDTH
)


NAV_ITEMS = [
    ("👤", "Profiles",     "profile"),
    ("⌨",  "Hotkeys",     "hotkeys"),
    ("🔍", "Zoom Behavior","zoom"),
    ("◎",  "Focus Overlay","focus"),
]


class MainWindow(QMainWindow):
    """
    IceZoom Settings Window.
    Structured as: [Sidebar] | [Content Panel]
    """

    def __init__(self, profile_manager, hotkey_manager, zoom_engine,
                 overlay_engine, pip_window, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._hm = hotkey_manager
        self._ze = zoom_engine
        self._oe = overlay_engine
        self._pip = pip_window
        self._zoom_active = False

        self.setWindowTitle(f"{APP_NAME} — Settings")
        self.setMinimumSize(QSize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT))
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self._build_ui()
        self._build_status_bar()
        self._connect_signals()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = self._build_sidebar()
        root.addWidget(self._sidebar)

        # Content area
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # Create panels
        self._profile_panel = ProfilePanel(self._pm)
        self._hotkey_panel  = HotkeyPanel(self._pm, self._hm)
        self._zoom_panel    = ZoomPanel(self._pm, self._ze)
        self._focus_panel   = FocusPanel(self._pm, self._oe)

        for panel in [self._profile_panel, self._hotkey_panel,
                      self._zoom_panel, self._focus_panel]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            panel.setContentsMargins(32, 28, 32, 28)
            scroll.setWidget(panel)
            self._stack.addWidget(scroll)

        # Default to Profiles panel
        self._navigate(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Brand header ──────────────────────────────────────────────────────
        brand = QFrame()
        brand.setObjectName("sidebar_brand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 18, 16, 14)
        brand_layout.setSpacing(2)

        name_lbl = QLabel("❄ ICEZOOM")
        name_lbl.setObjectName("brand_name")
        brand_layout.addWidget(name_lbl)

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setObjectName("brand_version")
        brand_layout.addWidget(ver_lbl)

        layout.addWidget(brand)

        # ── Global on/off toggle ──────────────────────────────────────────────
        toggle_frame = QFrame()
        toggle_frame.setStyleSheet("background: transparent; padding: 8px 16px;")
        t_layout = QHBoxLayout(toggle_frame)
        t_layout.setContentsMargins(0, 0, 0, 0)

        t_lbl = QLabel("Zoom Active")
        t_lbl.setStyleSheet("font-size: 12px; color: #8B949E;")
        t_layout.addWidget(t_lbl)
        t_layout.addStretch()

        self._global_toggle = ToggleSwitch(False)
        self._global_toggle.toggled.connect(self._on_global_toggle)
        t_layout.addWidget(self._global_toggle)
        layout.addWidget(toggle_frame)

        # ── Nav divider ───────────────────────────────────────────────────────
        nav_label = QLabel("SETTINGS")
        nav_label.setStyleSheet(
            "color: #484F58; font-size: 10px; font-weight: 700; "
            "letter-spacing: 1.5px; padding: 10px 16px 4px 16px;"
        )
        layout.addWidget(nav_label)

        # ── Nav buttons ───────────────────────────────────────────────────────
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(2)

        self._nav_buttons = []
        for i, (icon, label, _) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.clicked.connect(lambda checked, idx=i: self._navigate(idx))
            nav_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addWidget(nav_container)
        layout.addStretch()

        # ── Startup toggle ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("separator")
        layout.addWidget(sep)

        startup_frame = QFrame()
        startup_frame.setStyleSheet("background: transparent; padding: 6px 16px;")
        st_layout = QHBoxLayout(startup_frame)
        st_layout.setContentsMargins(0, 0, 0, 0)

        st_lbl = QLabel("Launch at startup")
        st_lbl.setStyleSheet("font-size: 12px; color: #8B949E;")
        st_layout.addWidget(st_lbl)
        st_layout.addStretch()

        self._startup_toggle = ToggleSwitch(self._pm.get("startup_with_windows", False))
        self._startup_toggle.toggled.connect(self._on_startup_toggle)
        st_layout.addWidget(self._startup_toggle)
        layout.addWidget(startup_frame)

        # ── Profile quick-display ─────────────────────────────────────────────
        self._active_profile_lbl = QLabel(f"● {self._pm.active_name()}")
        self._active_profile_lbl.setStyleSheet(
            "color: #00D4FF; font-size: 11px; font-weight: 600; "
            "padding: 6px 16px 12px 16px;"
        )
        layout.addWidget(self._active_profile_lbl)

        return sidebar

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage(
            f"Active Profile: {self._pm.active_name()}  |  Zoom: Inactive"
        )

    # ── Navigation ────────────────────────────────────────────────────────────

    # Ordered to match NAV_ITEMS / stack order
    _PANEL_REFRESH_MAP = [
        "_profile_panel",
        "_hotkey_panel",
        "_zoom_panel",
        "_focus_panel",
    ]

    def _navigate(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Re-sync the target panel from the authoritative profile state.
        # This prevents any stale widget values after tab switches.
        if 0 <= index < len(self._PANEL_REFRESH_MAP):
            panel = getattr(self, self._PANEL_REFRESH_MAP[index], None)
            if panel and hasattr(panel, "_refresh"):
                panel._refresh()

    # ── Signal Connections ────────────────────────────────────────────────────

    def _connect_signals(self):
        self._pm.profile_switched.connect(self._on_profile_switched)
        self._ze.zoom_factor_changed.connect(self._on_zoom_factor_changed)

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_profile_switched(self, name: str):
        self._active_profile_lbl.setText(f"● {name}")
        self._update_status()

    @pyqtSlot(float)
    def _on_zoom_factor_changed(self, factor: float):
        self._update_status()

    def _update_status(self):
        zoom_state = "Active" if self._zoom_active else "Inactive"
        factor = self._pm.get("zoom_factor", 2.0)
        self._status_bar.showMessage(
            f"Profile: {self._pm.active_name()}  |  "
            f"Zoom: {zoom_state} ({factor:.1f}×)  |  "
            f"Mode: {self._pm.get('zoom_behavior', 'Follow Mouse')}"
        )

    @pyqtSlot(bool)
    def _on_global_toggle(self, enabled: bool):
        self._zoom_active = enabled
        self._ze.set_active(enabled)
        if enabled:
            if self._pm.get("pip_mode", False):
                self._pip.show()
            else:
                self._oe.set_visible(True)
            self._ze.apply_mouse_sensitivity(True)
        else:
            self._oe.set_visible(False)
            self._pip.hide()
            self._ze.apply_mouse_sensitivity(False)
        self._update_status()

    def _on_startup_toggle(self, enabled: bool):
        self._pm.set("startup_with_windows", enabled)
        self._set_startup_registry(enabled)

    @staticmethod
    def _set_startup_registry(enabled: bool):
        """Add/remove IceZoom from Windows startup."""
        import sys
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, "IceZoom", 0, winreg.REG_SZ, sys.executable)
            else:
                try:
                    winreg.DeleteValue(key, "IceZoom")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    # ── Public helpers called by main controller ───────────────────────────────

    def set_global_toggle_state(self, enabled: bool):
        self._global_toggle.setChecked(enabled, emit=False)
        self._zoom_active = enabled
        self._update_status()

    def set_tray_toggle_callback(self, callback):
        """Let tray toggle connect to the same handler."""
        pass  # handled in main.py via signal routing

    # ── Close behaviour ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        """Minimize to tray instead of quitting."""
        event.ignore()
        self.hide()
