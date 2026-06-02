"""
IceZoom — Auto Profile Switcher
Polls the foreground window executable every 500ms.
When a match is found in any profile's auto_switch_apps list,
that profile is activated. On loss of focus, the previous profile
is restored.
"""
import os
import ctypes
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, QTimer

try:
    import win32process
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class AutoSwitcher(QThread):
    """
    Background thread that watches the Windows foreground window and
    auto-switches IceZoom profiles when a matching executable is detected.

    Signals
    -------
    switch_to_profile(name: str)
    """

    switch_to_profile = pyqtSignal(str)

    POLL_INTERVAL_MS = 500

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self._pm = profile_manager
        self._running = True
        self._previous_profile: Optional[str] = None
        self._auto_switched = False
        self._last_exe: str = ""

    def run(self):
        if not HAS_WIN32:
            return  # Win32 not available; skip silently

        while self._running:
            self._check()
            self.msleep(self.POLL_INTERVAL_MS)

    def _check(self):
        try:
            exe = self._get_foreground_exe()
        except Exception:
            return

        if exe == self._last_exe:
            return
        self._last_exe = exe

        # Search all profiles for a match
        for profile_name in self._pm.list_profiles():
            apps = self._pm._data[profile_name].get("auto_switch_apps", [])
            if exe.lower() in [a.lower() for a in apps]:
                if self._pm.active_name() != profile_name:
                    if not self._auto_switched:
                        self._previous_profile = self._pm.active_name()
                    self._auto_switched = True
                    self.switch_to_profile.emit(profile_name)
                return

        # No match — restore previous profile if we auto-switched
        if self._auto_switched:
            self._auto_switched = False
            if self._previous_profile and self._previous_profile != self._pm.active_name():
                self.switch_to_profile.emit(self._previous_profile)
            self._previous_profile = None

    @staticmethod
    def _get_foreground_exe() -> str:
        """Return the basename of the foreground window's process executable."""
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return ""
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
        )
        if not handle:
            return ""
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.psapi.GetModuleFileNameExW(handle, None, buf, 1024)
        ctypes.windll.kernel32.CloseHandle(handle)
        return os.path.basename(buf.value)

    def stop(self):
        self._running = False
        self.wait(1000)
