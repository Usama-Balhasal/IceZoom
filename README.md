# IceZoom 🔍❄

**Desktop Magnification & Screen-Focusing Utility for Windows**

---

## Features

### Core
- 🔒 **Multiple Configuration Profiles** — Create, rename, duplicate, delete; all settings persist per-profile
- ⌨ **Customizable Global Hotkeys** — Click-to-record any key combination
- 🔍 **Real-Time Screen Magnification** — Follow Mouse or Fixed Position modes
- ◎ **Focus Shape Overlay** — Circle or Square vignette with background dim, outline, crosshair
- 🎨 **Color & Opacity Controls** — Full customization of all overlay elements

### Advanced
- 📦 **Picture-in-Picture Mode** — Floating draggable/resizable zoom window
- 🔄 **Auto-Profile Switching** — Automatically activates profiles when registered apps gain focus
- 🔔 **System Tray Integration** — Quick-switch profiles, enable/disable, minimize to tray
- 🚀 **Launch at Windows Startup** — Optional registry integration

---

## Requirements

- **Python 3.11+**
- **Windows 10/11** (Win32 API features)

## Installation

```bash
pip install -r requirements.txt
python main.py
```

---

## Default Hotkeys

| Action | Default |
|---|---|
| Global Toggle | `Shift + Alt + X` |
| Toggle Zoom (Hold) | `Shift + Right Mouse Button` |
| Increase Zoom | `Shift + Up Arrow` |
| Decrease Zoom | `Shift + Down Arrow` |
| Reset Zoom | `Shift + R` |

All hotkeys are fully customizable per-profile in **Settings → Hotkeys**.

---

## Project Structure

```
IceZoom/
├── main.py                   # Entry point
├── app/
│   ├── core/
│   │   ├── profile_manager.py
│   │   ├── hotkey_manager.py
│   │   ├── zoom_engine.py
│   │   ├── overlay_engine.py
│   │   ├── pip_window.py
│   │   └── auto_switcher.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── tray_icon.py
│   │   ├── panels/
│   │   │   ├── profile_panel.py
│   │   │   ├── hotkey_panel.py
│   │   │   ├── zoom_panel.py
│   │   │   └── focus_panel.py
│   │   └── widgets/
│   │       ├── toggle_switch.py
│   │       ├── hotkey_widget.py
│   │       └── color_picker.py
│   └── utils/
│       ├── constants.py
│       └── theme.py
├── assets/
│   └── icon.png
└── requirements.txt
```

---

## Profile Storage

Profiles are stored as JSON files in `~/.icezoom/profiles/`.
You can manually edit them or use **Export/Import** (`.icezoom` bundle) from the Profiles panel.

---

## License

MIT
