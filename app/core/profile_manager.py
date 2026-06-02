"""
IceZoom — Profile Manager
Handles create / delete / duplicate / rename / switch / persist of profiles.
"""
import json
import os
import shutil
import copy
from typing import Dict, Any, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.utils.constants import (
    PROFILES_DIR, GLOBAL_CONFIG_FILE, DEFAULT_PROFILE
)


class ProfileManager(QObject):
    """
    Singleton-style manager for IceZoom profiles.

    Signals
    -------
    profile_switched(name)   — Emitted after active profile is changed.
    profiles_changed()       — Emitted when the profile list changes (add/del/dup/ren).
    setting_changed(key, val)— Emitted when any setting on the active profile changes.
    """

    profile_switched  = pyqtSignal(str)
    profiles_changed  = pyqtSignal()
    setting_changed   = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_name: str = "Default"
        self._data: Dict[str, Any] = {}
        self._load_all()

    # ── Persistence ─────────────────────────────────────────────────────────

    def _profile_path(self, name: str) -> str:
        safe = name.replace(" ", "_").replace("/", "_")
        return os.path.join(PROFILES_DIR, f"{safe}.json")

    def _load_all(self):
        """Load global config + all profiles from disk."""
        # Load global config
        if os.path.exists(GLOBAL_CONFIG_FILE):
            try:
                with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    gc = json.load(f)
                    self._active_name = gc.get("active_profile", "Default")
            except Exception:
                self._active_name = "Default"

        # Load all profile files
        self._data = {}
        for fname in os.listdir(PROFILES_DIR):
            if fname.endswith(".json"):
                path = os.path.join(PROFILES_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        profile = json.load(f)
                    name = profile.get("_name", fname[:-5].replace("_", " "))
                    self._data[name] = self._merge_defaults(profile)
                except Exception:
                    pass

        # Ensure at least one profile exists
        if not self._data:
            self._data["Default"] = self._new_profile("Default")
            self._save_profile("Default")

        # Ensure active profile is valid
        if self._active_name not in self._data:
            self._active_name = next(iter(self._data))

        self._save_global_config()

    def _new_profile(self, name: str) -> Dict[str, Any]:
        p = copy.deepcopy(DEFAULT_PROFILE)
        p["_name"] = name
        return p

    def _merge_defaults(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing keys with defaults (forward-compat for new settings)."""
        merged = copy.deepcopy(DEFAULT_PROFILE)
        merged.update(profile)
        return merged

    def _save_profile(self, name: str):
        if name not in self._data:
            return
        path = self._profile_path(name)
        self._data[name]["_name"] = name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data[name], f, indent=2)

    def _save_global_config(self):
        cfg = {"active_profile": self._active_name}
        with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    # ── Public API ───────────────────────────────────────────────────────────

    def list_profiles(self) -> List[str]:
        return sorted(self._data.keys())

    def active_name(self) -> str:
        return self._active_name

    def active_profile(self) -> Dict[str, Any]:
        return self._data[self._active_name]

    def get(self, key: str, default=None):
        return self.active_profile().get(key, default)

    def set(self, key: str, value: Any):
        """Update a setting in the active profile and persist."""
        self._data[self._active_name][key] = value
        self._save_profile(self._active_name)
        self.setting_changed.emit(key, value)

    def set_hotkey(self, action_id: str, combo: str):
        hotkeys = self.get("hotkeys", {})
        hotkeys[action_id] = combo
        self.set("hotkeys", hotkeys)

    def switch(self, name: str):
        if name not in self._data:
            return
        self._active_name = name
        self._save_global_config()
        self.profile_switched.emit(name)

    def create(self, name: str) -> bool:
        if name in self._data or not name.strip():
            return False
        self._data[name] = self._new_profile(name)
        self._save_profile(name)
        self.profiles_changed.emit()
        return True

    def delete(self, name: str) -> bool:
        if name not in self._data or len(self._data) <= 1:
            return False
        path = self._profile_path(name)
        if os.path.exists(path):
            os.remove(path)
        del self._data[name]
        if self._active_name == name:
            self._active_name = next(iter(self._data))
            self._save_global_config()
        self.profiles_changed.emit()
        return True

    def duplicate(self, name: str, new_name: str) -> bool:
        if name not in self._data or new_name in self._data or not new_name.strip():
            return False
        self._data[new_name] = copy.deepcopy(self._data[name])
        self._data[new_name]["_name"] = new_name
        self._save_profile(new_name)
        self.profiles_changed.emit()
        return True

    def rename(self, old_name: str, new_name: str) -> bool:
        if old_name not in self._data or new_name in self._data or not new_name.strip():
            return False
        old_path = self._profile_path(old_name)
        self._data[new_name] = self._data.pop(old_name)
        self._data[new_name]["_name"] = new_name
        if os.path.exists(old_path):
            os.remove(old_path)
        self._save_profile(new_name)
        if self._active_name == old_name:
            self._active_name = new_name
            self._save_global_config()
        self.profiles_changed.emit()
        return True

    def export_all(self, path: str):
        """Export all profiles as a ZIP-like .icezoom bundle."""
        import zipfile
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name in self._data:
                profile_path = self._profile_path(name)
                if os.path.exists(profile_path):
                    zf.write(profile_path, arcname=os.path.basename(profile_path))

    def import_bundle(self, path: str):
        """Import profiles from a .icezoom bundle."""
        import zipfile
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(PROFILES_DIR)
        self._load_all()
        self.profiles_changed.emit()

    def add_auto_switch_app(self, exe: str):
        apps = self.get("auto_switch_apps", [])
        if exe not in apps:
            apps.append(exe)
            self.set("auto_switch_apps", apps)

    def remove_auto_switch_app(self, exe: str):
        apps = self.get("auto_switch_apps", [])
        if exe in apps:
            apps.remove(exe)
            self.set("auto_switch_apps", apps)
