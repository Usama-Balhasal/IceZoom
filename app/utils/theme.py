"""
IceZoom — QSS Dark Theme Stylesheet
"""
from app.utils.constants import (
    ICE_BLUE, ICE_BLUE_DIM, ICE_ACCENT,
    BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER_COLOR, DANGER_COLOR, SUCCESS_COLOR, WARNING_COLOR,
)

STYLESHEET = f"""
/* ── Global ──────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {BG_DARK};
}}

/* ── Scroll Areas ─────────────────────────────────────────────────────────── */
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {ICE_BLUE_DIM};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ICE_BLUE};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_PANEL};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {ICE_BLUE_DIM};
    border-radius: 3px;
}}

/* ── Labels ───────────────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
}}
QLabel#heading {{
    font-size: 18px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    padding-bottom: 4px;
}}
QLabel#subheading {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
    padding-bottom: 12px;
}}
QLabel#section_title {{
    font-size: 11px;
    font-weight: 700;
    color: {ICE_BLUE};
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 8px 0 4px 0;
}}
QLabel#muted {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}
QLabel#value_label {{
    color: {ICE_BLUE};
    font-weight: 600;
    min-width: 40px;
}}
QLabel#danger {{
    color: {DANGER_COLOR};
    font-size: 11px;
}}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {ICE_BLUE};
    color: {ICE_BLUE};
}}
QPushButton:pressed {{
    background-color: {BG_ACTIVE};
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    border-color: {TEXT_MUTED};
}}
QPushButton#primary {{
    background-color: {ICE_BLUE};
    color: #000000;
    border: none;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: {ICE_ACCENT};
    color: #000000;
}}
QPushButton#danger {{
    background-color: transparent;
    color: {DANGER_COLOR};
    border: 1px solid {DANGER_COLOR};
}}
QPushButton#danger:hover {{
    background-color: {DANGER_COLOR};
    color: #ffffff;
}}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    padding: 4px;
    border-radius: 4px;
}}
QPushButton#icon_btn:hover {{
    background-color: {BG_HOVER};
}}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
QFrame#sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER_COLOR};
}}
QFrame#sidebar_brand {{
    background: transparent;
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 12px;
}}
QLabel#brand_name {{
    font-size: 20px;
    font-weight: 800;
    color: {ICE_BLUE};
    letter-spacing: 2px;
}}
QLabel#brand_version {{
    font-size: 10px;
    color: {TEXT_MUTED};
}}

/* ── Sidebar Navigation Buttons ──────────────────────────────────────────── */
QPushButton#nav_btn {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_btn:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton#nav_btn[active="true"] {{
    background-color: {BG_ACTIVE};
    color: {ICE_BLUE};
    font-weight: 700;
    border-left: 3px solid {ICE_BLUE};
}}

/* ── Profile List ─────────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    color: {TEXT_PRIMARY};
    padding: 10px 12px;
    border-radius: 6px;
    margin: 2px 0;
}}
QListWidget::item:hover {{
    background-color: {BG_HOVER};
}}
QListWidget::item:selected {{
    background-color: {BG_ACTIVE};
    color: {ICE_BLUE};
    font-weight: 600;
}}

/* ── ComboBox ─────────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 7px 12px;
    min-width: 140px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {ICE_BLUE};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {ICE_BLUE};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    selection-background-color: {BG_ACTIVE};
    selection-color: {ICE_BLUE};
    outline: none;
    padding: 4px;
}}

/* ── Sliders ──────────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {BG_HOVER};
    height: 4px;
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ICE_BLUE_DIM}, stop:1 {ICE_BLUE});
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ICE_BLUE};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    border: 2px solid {BG_PANEL};
}}
QSlider::handle:horizontal:hover {{
    background: {ICE_ACCENT};
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}}

/* ── Line Edits ────────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    selection-background-color: {ICE_BLUE};
    selection-color: #000000;
}}
QLineEdit:focus {{
    border-color: {ICE_BLUE};
    background-color: {BG_PANEL};
}}
QLineEdit:disabled {{
    color: {TEXT_MUTED};
    background-color: {BG_PANEL};
    border-color: {TEXT_MUTED};
}}

/* ── Spin Boxes ───────────────────────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 8px;
    padding-right: 22px;
    font-size: 13px;
    selection-background-color: {ICE_BLUE};
    selection-color: #000000;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {ICE_BLUE};
    background-color: {BG_PANEL};
}}
QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {TEXT_MUTED};
    background-color: {BG_PANEL};
    border-color: {TEXT_MUTED};
}}
/* Up button */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    background-color: {BG_CARD};
    border-left: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    border-top-right-radius: 5px;
    width: 20px;
    height: 50%;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background-color: {BG_HOVER};
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{
    background-color: {ICE_BLUE_DIM};
}}
/* Up arrow indicator — clean triangle matching dark palette */
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left:   4px solid transparent;
    border-right:  4px solid transparent;
    border-bottom: 5px solid {TEXT_SECONDARY};
}}
QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {{
    border-bottom-color: {ICE_BLUE};
}}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled {{
    border-bottom-color: {TEXT_MUTED};
}}
/* Down button */
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    background-color: {BG_CARD};
    border-left: 1px solid {BORDER_COLOR};
    border-top: 1px solid {BORDER_COLOR};
    border-bottom-right-radius: 5px;
    width: 20px;
    height: 50%;
}}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {BG_HOVER};
}}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background-color: {ICE_BLUE_DIM};
}}
/* Down arrow indicator — clean triangle matching dark palette */
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left:  4px solid transparent;
    border-right: 4px solid transparent;
    border-top:   5px solid {TEXT_SECONDARY};
}}
QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {{
    border-top-color: {ICE_BLUE};
}}
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
    border-top-color: {TEXT_MUTED};
}}

/* ── Group Box / Cards ────────────────────────────────────────────────────── */
QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 4px;
}}
QFrame#separator {{
    background-color: {BORDER_COLOR};
    max-height: 1px;
    min-height: 1px;
}}

/* ── Tool Tips ────────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ── Status Bar ───────────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── Tab Widget (unused but available) ───────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    background: {BG_PANEL};
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_SECONDARY};
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    color: {ICE_BLUE};
    border-bottom-color: {ICE_BLUE};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}

/* ── CheckBox ─────────────────────────────────────────────────────────────── */
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER_COLOR};
    border-radius: 4px;
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ICE_BLUE};
    border-color: {ICE_BLUE};
}}
"""

def safe_font_size(size: int, fallback: int = 11) -> int:
    """
    Guard helper — ensures a font point size is always > 0.
    If the computed size is 0 or negative, returns `fallback` (default 11).
    Use this whenever deriving a QFont point size programmatically.
    """
    return size if size > 0 else fallback


def apply_theme(app):
    """Apply the IceZoom dark theme to the QApplication."""
    app.setStyleSheet(STYLESHEET)
