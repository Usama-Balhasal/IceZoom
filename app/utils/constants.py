"""
IceZoom — Application Constants & Default Settings
"""
from dataclasses import dataclass, field
from typing import List

APP_NAME = "IceZoom"
APP_VERSION = "1.0.0"
ORG_NAME = "IceZoom"

# ── Paths ──────────────────────────────────────────────────────────────────────
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".icezoom")
PROFILES_DIR = os.path.join(CONFIG_DIR, "profiles")
GLOBAL_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

os.makedirs(PROFILES_DIR, exist_ok=True)

# ── Default Hotkeys ────────────────────────────────────────────────────────────
@dataclass
class HotkeyDefault:
    action_id: str
    display_name: str
    description: str
    default_combo: str      # Human-readable, e.g. "shift+alt+x"
    hold_mode: bool = False

HOTKEY_DEFAULTS: List[HotkeyDefault] = [
    HotkeyDefault(
        action_id="global_toggle",
        display_name="Global Toggle",
        description="Completely enable / disable IceZoom",
        default_combo="shift+alt+x",
    ),
    HotkeyDefault(
        action_id="toggle_zoom_hold",
        display_name="Toggle Zoom (Hold)",
        description="Activate zoom only while key is held",
        default_combo="shift+Mouse_RMB",
        hold_mode=True,
    ),
    HotkeyDefault(
        action_id="increase_zoom",
        display_name="Increase Zoom",
        description="Increment zoom by step amount",
        default_combo="shift+up",
    ),
    HotkeyDefault(
        action_id="decrease_zoom",
        display_name="Decrease Zoom",
        description="Decrement zoom by step amount",
        default_combo="shift+down",
    ),
    HotkeyDefault(
        action_id="reset_zoom",
        display_name="Reset Zoom",
        description="Restore zoom factor to baseline",
        default_combo="shift+r",
    ),
    HotkeyDefault(
        action_id="quit_app",
        display_name="Quit Application",
        description="Close IceZoom completely (exits the system tray)",
        default_combo="",
    ),
]

# ── Default Profile Settings ────────────────────────────────────────────────────
DEFAULT_PROFILE = {
    # Hotkeys
    "hotkeys": {h.action_id: h.default_combo for h in HOTKEY_DEFAULTS},

    # Zoom Behavior
    "zoom_behavior": "Follow Mouse",       # "Follow Mouse" | "Fixed Position"
    "zoom_fixed_x": 960,
    "zoom_fixed_y": 540,
    "zoom_factor": 2.0,
    "zoom_step": 0.3,
    "zoom_min": 1.0,
    "zoom_max": 10.0,
    "zoom_animations": True,
    "zoom_mouse_sensitivity": True,

    # Focus Shape Overlay
    "focus_enabled": True,
    "focus_shape": "Circle",               # "Circle" | "Square"
    "focus_size": 300,
    "focus_bg_enabled": True,
    "focus_bg_color": "#000000",
    "focus_bg_opacity": 0.55,
    "focus_outline_enabled": True,
    "focus_outline_color": "#00D4FF",
    "focus_outline_width": 3,
    "focus_outline_opacity": 1.0,

    # Crosshair
    "crosshair_enabled": False,
    "crosshair_color": "#FF4444",
    "crosshair_opacity": 0.9,
    "crosshair_size": 20,
    "crosshair_thickness": 2,

    # PiP
    "pip_mode": False,
    "pip_x": 100,
    "pip_y": 100,
    "pip_width": 400,
    "pip_height": 300,

    # Auto-switch apps
    "auto_switch_apps": [],               # list of exe basenames e.g. ["minecraft.exe"]

    # Bonus
    "startup_with_windows": False,
}

# ── UI Dimensions ───────────────────────────────────────────────────────────────
MAIN_WINDOW_WIDTH  = 920
MAIN_WINDOW_HEIGHT = 640
SIDEBAR_WIDTH      = 220

# ── Zoom Capture Region Size (pixels on screen, before upscale) ────────────────
CAPTURE_BASE_SIZE = 400   # width & height of captured region
OVERLAY_FPS       = 60

# ── Colors (reused in theme) ────────────────────────────────────────────────────
ICE_BLUE       = "#00D4FF"
ICE_BLUE_DIM   = "#007F99"
ICE_ACCENT     = "#00FFCC"
BG_DARK        = "#1C2029"   # cohesive dark base — replaces #0D1117
BG_PANEL       = "#161B22"
BG_CARD        = "#1c2029"
BG_HOVER       = "#21262D"
BG_ACTIVE      = "#1A3040"
TEXT_PRIMARY   = "#E6EDF3"
TEXT_SECONDARY = "#8B949E"
TEXT_MUTED     = "#484F58"
BORDER_COLOR   = "#30363D"
DANGER_COLOR   = "#F85149"
SUCCESS_COLOR  = "#3FB950"
WARNING_COLOR  = "#D29922"
