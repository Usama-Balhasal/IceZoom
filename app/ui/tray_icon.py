"""
IceZoom — System Tray Icon & Quick-Switch Menu
"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QActionGroup
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from app.utils.constants import APP_NAME


class TrayIcon(QSystemTrayIcon):
    """
    System tray icon with:
    - Left-click: show/hide settings window
    - Right-click menu: enable/disable, profile quick-switch, settings, quit
    """
    show_settings    = pyqtSignal()
    quit_requested   = pyqtSignal()
    profile_selected = pyqtSignal(str)
    toggle_requested = pyqtSignal()

    def __init__(self, icon: QIcon, profile_manager, parent=None):
        super().__init__(icon, parent)
        self._pm = profile_manager
        self._enabled = True
        self._profile_actions: dict[str, QAction] = {}
        self._build_menu()
        self.activated.connect(self._on_activated)
        self._pm.profiles_changed.connect(self._rebuild_profile_menu)
        self._pm.profile_switched.connect(self._on_profile_switched)

    def _build_menu(self):
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #161B22;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #21262D;
                color: #00D4FF;
            }
            QMenu::separator {
                height: 1px;
                background: #30363D;
                margin: 4px 8px;
            }
            QMenu::indicator {
                width: 14px;
                height: 14px;
            }
        """)

        # Status
        self._status_action = QAction("❄  IceZoom — Active", self)
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)

        self._menu.addSeparator()

        # Toggle enable/disable
        self._toggle_action = QAction("⏸  Disable IceZoom", self)
        self._toggle_action.triggered.connect(self._on_toggle)
        self._menu.addAction(self._toggle_action)

        self._menu.addSeparator()

        # Profiles submenu
        self._profiles_label = QAction("PROFILES", self)
        self._profiles_label.setEnabled(False)
        self._menu.addAction(self._profiles_label)

        self._profile_group = QActionGroup(self)
        self._profile_group.setExclusive(True)
        self._profile_actions_menu = QMenu("Switch Profile", self._menu)
        self._rebuild_profile_menu()
        self._menu.addMenu(self._profile_actions_menu)

        self._menu.addSeparator()

        # Settings
        settings_action = QAction("⚙  Open Settings", self)
        settings_action.triggered.connect(self.show_settings)
        self._menu.addAction(settings_action)

        self._menu.addSeparator()

        # Quit
        quit_action = QAction("✕  Quit IceZoom", self)
        quit_action.triggered.connect(self.quit_requested)
        self._menu.addAction(quit_action)

        self.setContextMenu(self._menu)
        self.setToolTip(f"{APP_NAME} — Active")

    def _rebuild_profile_menu(self):
        self._profile_actions_menu.clear()
        self._profile_actions = {}

        for name in self._pm.list_profiles():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(name == self._pm.active_name())
            action.triggered.connect(lambda checked, n=name: self._on_profile_action(n))
            self._profile_group.addAction(action)
            self._profile_actions_menu.addAction(action)
            self._profile_actions[name] = action

    def _on_profile_action(self, name: str):
        self.profile_selected.emit(name)

    def _on_profile_switched(self, name: str):
        for n, action in self._profile_actions.items():
            action.setChecked(n == name)
        self.setToolTip(f"{APP_NAME} — {name}")

    def _on_toggle(self):
        self._enabled = not self._enabled
        if self._enabled:
            self._toggle_action.setText("⏸  Disable IceZoom")
            self._status_action.setText("❄  IceZoom — Active")
            self.setToolTip(f"{APP_NAME} — Active")
        else:
            self._toggle_action.setText("▶  Enable IceZoom")
            self._status_action.setText("❄  IceZoom — Disabled")
            self.setToolTip(f"{APP_NAME} — Disabled")
        self.toggle_requested.emit()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings.emit()

    def set_enabled_state(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self._toggle_action.setText("⏸  Disable IceZoom")
            self._status_action.setText("❄  IceZoom — Active")
        else:
            self._toggle_action.setText("▶  Enable IceZoom")
            self._status_action.setText("❄  IceZoom — Disabled")
