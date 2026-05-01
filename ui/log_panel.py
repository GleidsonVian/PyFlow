from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


LOG_ICONS = {
    "info":    ("💬", "#89b4fa"),
    "running": ("⏳", "#fab387"),
    "success": ("✅", "#a6e3a1"),
    "error":   ("❌", "#f38ba8"),
    "divider": ("─",  "#45475a"),
}


class LogEntry(QWidget):
    def __init__(self, kind: str, message: str):
        super().__init__()
        icon, color = LOG_ICONS.get(kind, LOG_ICONS["info"])
        timestamp = datetime.now().strftime("%H:%M:%S")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(20)
        lbl_icon.setAlignment(Qt.AlignCenter)

        lbl_time = QLabel(timestamp)
        lbl_time.setFixedWidth(58)
        lbl_time.setStyleSheet("color: #45475a; font-size: 11px;")

        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"color: {color}; font-size: 12px;")

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_time)
        layout.addWidget(lbl_msg, 1)


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("log_panel")
        self.setFixedHeight(180)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("log_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 6, 12, 6)

        title = QLabel("📋  Log de execução")
        title.setObjectName("log_title")

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setObjectName("log_btn_clear")
        self.btn_clear.setFixedHeight(24)
        self.btn_clear.clicked.connect(self.clear)

        h.addWidget(title)
        h.addStretch()
        h.addWidget(self.btn_clear)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("log_sep")
        root.addWidget(sep)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("log_scroll")
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content.setObjectName("log_content")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

    def log(self, kind: str, message: str):
        entry = LogEntry(kind, message)
        self.content_layout.addWidget(entry)
        # Auto-scroll para o final
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def log_run_start(self, total: int):
        self._add_divider(f"▶  Iniciando execução — {total} passo(s)")

    def log_run_end(self, ok: int, total: int):
        kind = "success" if ok == total else "error"
        self._add_divider(f"{'✓' if ok == total else '✗'}  Concluído: {ok}/{total} com sucesso")

    def _add_divider(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("log_divider")
        lbl.setContentsMargins(8, 4, 8, 4)
        self.content_layout.addWidget(lbl)
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _apply_styles(self):
        self.setStyleSheet("""
            #log_panel { background-color: #11111b; }
            #log_header { background-color: #11111b; }
            #log_title { font-size: 12px; font-weight: 600; color: #6c7086; }
            #log_sep { color: #313244; }
            #log_scroll, #log_content { background-color: #11111b; border: none; }
            #log_btn_clear {
                background-color: #313244;
                color: #6c7086;
                border: none;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }
            #log_btn_clear:hover { background-color: #45475a; color: #cdd6f4; }
            #log_divider {
                color: #585b70;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                background-color: #1e1e2e;
                border-left: 2px solid #45475a;
                margin: 4px 8px;
            }
        """)