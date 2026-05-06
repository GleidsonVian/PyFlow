"""
ThemeManager — tema visual do PyFlow RPA (dark only).
"""

DARK = {
    "bg":           "#1e1e2e",
    "surface":      "#181825",
    "overlay":      "#313244",
    "muted":        "#45475a",
    "subtle":       "#6c7086",
    "text":         "#cdd6f4",
    "text2":        "#a6adc8",
    "accent":       "#cba6f7",
    "green":        "#a6e3a1",
    "blue":         "#89b4fa",
    "red":          "#f38ba8",
    "orange":       "#fab387",
    "border":       "#313244",
    "toolbar":      "#181825",
    "btn_sec":      "#313244",
    "btn_sec_hov":  "#45475a",
    "scrollbar":    "#45475a",
    "run_btn":      "#a6e3a1",
    "run_btn_text": "#1e1e2e",
}


def colors() -> dict:
    return DARK


def build_main_qss() -> str:
    c = DARK
    return f"""
QMainWindow, QWidget {{
    background-color: {c['bg']};
    color: {c['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QMenuBar {{
    background-color: {c['surface']};
    color: {c['text']};
    padding: 2px;
    border-bottom: 1px solid {c['border']};
}}
QMenuBar::item:selected {{ background-color: {c['overlay']}; border-radius: 4px; }}
QMenu {{
    background-color: {c['bg']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 4px;
    color: {c['text']};
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {c['overlay']}; }}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {c['accent']};
    selection-color: {c['bg']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c['accent']};
}}
QComboBox {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    selection-background-color: {c['overlay']};
}}

#toolbar {{ background-color: {c['toolbar']}; border-bottom: 1px solid {c['border']}; }}
#app_title {{ font-size: 15px; font-weight: 600; color: {c['accent']}; }}
#retry_badge {{
    font-size: 11px; font-weight: 600; color: {c['orange']};
    background-color: {c['surface']}; border: 1px solid {c['orange']};
    border-radius: 4px; padding: 2px 8px;
}}

QPushButton {{
    border: none; border-radius: 6px;
    padding: 6px 14px; font-size: 12px; font-weight: 500;
}}
#btn_run {{ background-color: {c['run_btn']}; color: {c['run_btn_text']}; font-weight: 700; }}
#btn_run:hover {{ background-color: {c['green']}; }}
#btn_run:disabled {{ background-color: {c['muted']}; color: {c['subtle']}; }}
#btn_debug {{ background-color: {c['surface']}; color: {c['green']}; border: 1px solid {c['green']}; font-weight: 600; }}
#btn_debug:hover {{ background-color: {c['overlay']}; }}
#btn_debug:disabled {{ background-color: {c['muted']}; color: {c['subtle']}; border-color: {c['muted']}; }}
#btn_stop {{ background-color: {c['red']}; color: {c['run_btn_text']}; font-weight: 600; }}
#btn_stop:disabled {{ background-color: {c['muted']}; color: {c['subtle']}; }}
#btn_secondary {{ background-color: {c['btn_sec']}; color: {c['text']}; }}
#btn_secondary:hover {{ background-color: {c['btn_sec_hov']}; }}
#btn_export {{ background-color: {c['surface']}; color: {c['blue']}; border: 1px solid {c['blue']}; }}
#btn_record {{ background-color: {c['surface']}; color: {c['red']}; border: 1px solid {c['red']}; font-weight: 700; }}
#btn_record:hover {{ background-color: {c['overlay']}; }}
#btn_palette {{ background-color: {c['surface']}; color: {c['accent']}; border: 1px solid {c['accent']}; font-weight: 600; }}
#btn_palette:hover {{ background-color: {c['overlay']}; }}
#btn_templates {{ background-color: {c['surface']}; color: {c['orange']}; border: 1px solid {c['orange']}; }}
#btn_templates:hover {{ background-color: {c['overlay']}; }}
#btn_scheduler {{ background-color: {c['btn_sec']}; color: {c['text']}; }}
#btn_scheduler:hover {{ background-color: {c['btn_sec_hov']}; }}
#btn_api {{ background-color: {c['surface']}; color: {c['blue']}; border: 1px solid {c['blue']}; font-weight: 600; }}
#btn_api:hover {{ background-color: {c['overlay']}; }}
#btn_assets {{ background-color: {c['surface']}; color: {c['accent']}; border: 1px solid {c['accent']}; font-weight: 600; }}
#btn_assets:hover {{ background-color: {c['overlay']}; }}
#btn_vars {{ background-color: {c['surface']}; color: {c['green']}; border: 1px solid {c['green']}; }}
#btn_vars:checked {{ background-color: {c['green']}; color: {c['run_btn_text']}; }}
#btn_settings {{ background-color: {c['btn_sec']}; color: {c['subtle']}; font-size: 15px; }}
#btn_settings:hover {{ background-color: {c['btn_sec_hov']}; color: {c['text']}; }}
#btn_headless_off {{ background-color: {c['surface']}; color: {c['blue']}; border: 1px solid {c['border']}; font-size: 12px; }}
#btn_headless_off:hover {{ background-color: {c['overlay']}; border-color: {c['blue']}; }}
#btn_headless_on {{ background-color: {c['overlay']}; color: {c['orange']}; border: 1px solid {c['orange']}; font-size: 12px; font-weight: 700; }}
#btn_headless_on:hover {{ background-color: #3a2a1c; }}

#right_panel {{ background-color: {c['surface']}; border-left: 1px solid {c['border']}; }}
QSplitter::handle {{ background-color: {c['border']}; width: 2px; }}
QSplitter::handle:hover {{ background-color: {c['accent']}; }}
#status_bar {{
    background-color: {c['surface']};
    color: {c['subtle']};
    border-top: 1px solid {c['border']};
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: {c['bg']}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c['scrollbar']}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {c['bg']}; height: 8px; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c['scrollbar']}; border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QTabWidget::pane {{ border: none; background-color: {c['bg']}; }}
QTabBar::tab {{
    background-color: {c['surface']}; color: {c['subtle']};
    padding: 7px 14px; font-size: 12px; border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{ color: {c['accent']}; border-bottom: 2px solid {c['accent']}; }}
QTabBar::tab:hover {{ color: {c['text']}; }}

QListWidget {{
    background-color: {c['surface']}; color: {c['text']};
    border: 1px solid {c['border']}; border-radius: 6px;
}}
QListWidget::item:selected {{ background-color: {c['overlay']}; border-radius: 4px; }}
QListWidget::item:hover {{ background-color: {c['overlay']}; border-radius: 4px; }}

QCheckBox {{ color: {c['text']}; spacing: 6px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid {c['border']}; background-color: {c['surface']};
}}
QCheckBox::indicator:checked {{ background-color: {c['accent']}; border-color: {c['accent']}; }}

QLabel {{ color: {c['text']}; background: transparent; }}
"""
