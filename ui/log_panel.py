"""
Log panel melhorado do PyFlow RPA.
Filtros por tipo, busca, copiar e exportar como TXT.
Coloque em: ui/log_panel.py
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QFrame, QFileDialog, QApplication,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont


LOG_TYPES = {
    "info":    {"color": "#89b4fa", "bg": "#1a2a40", "icon": "ℹ"},
    "running": {"color": "#cba6f7", "bg": "#2a1e3f", "icon": "▶"},
    "success": {"color": "#a6e3a1", "bg": "#1a2e20", "icon": "✓"},
    "error":   {"color": "#f38ba8", "bg": "#2e1a1a", "icon": "✗"},
    "warning": {"color": "#fab387", "bg": "#2e2010", "icon": "⚠"},
    "system":  {"color": "#6c7086", "bg": "#1e1e2e", "icon": "⚙"},
}

FILTER_BUTTONS = [
    ("Todos",  None),
    ("✓ OK",   "success"),
    ("✗ Erro", "error"),
    ("▶ Exec", "running"),
    ("ℹ Info", "info"),
    ("⚙ Sist", "system"),
]


class LogEntry:
    def __init__(self, level: str, message: str, timestamp: str):
        self.level     = level
        self.message   = message
        self.timestamp = timestamp

    def to_text(self) -> str:
        return f"[{self.timestamp}] [{self.level.upper():7}] {self.message}"


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
        self.setFixedHeight(180)
        self._entries: list[LogEntry] = []
        self._active_filter = None
        self._search_text   = ""
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("log_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(10, 5, 8, 5)
        h.setSpacing(5)

        lbl = QLabel("📋  Log")
        lbl.setObjectName("log_title")
        h.addWidget(lbl)

        # Filtros por tipo
        self._filter_btns = {}
        for label, level in FILTER_BUTTONS:
            btn = QPushButton(label)
            btn.setObjectName("log_filter_btn")
            btn.setCheckable(True)
            btn.setChecked(level is None)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda checked, lv=level: self._on_filter(lv))
            self._filter_btns[str(level)] = btn
            h.addWidget(btn)

        h.addStretch()

        # Busca
        self.search = QLineEdit()
        self.search.setObjectName("log_search")
        self.search.setPlaceholderText("🔍 Filtrar...")
        self.search.setFixedWidth(150)
        self.search.setFixedHeight(22)
        self.search.textChanged.connect(self._on_search)
        h.addWidget(self.search)

        # Contador
        self.lbl_count = QLabel("0")
        self.lbl_count.setObjectName("log_count")
        h.addWidget(self.lbl_count)

        # Ações
        for text, tip, slot in [
            ("⎘ Copiar",   "Copiar log visível",      self._on_copy),
            ("💾 Exportar", "Exportar como .txt",      self._on_export),
            ("🗑",          "Limpar log",              self.clear),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("log_action_btn" if len(text) > 2 else "log_clear_btn")
            btn.setFixedHeight(22)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("log_sep")
        root.addWidget(sep)

        # ── Lista ─────────────────────────────────────────────────────
        self.list = QListWidget()
        self.list.setObjectName("log_list")
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self.list, 1)

    # ── API pública ───────────────────────────────────────────────────

    def log(self, level: str, message: str):
        ts    = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(level, message, ts)
        self._entries.append(entry)
        if self._matches(entry):
            self.list.addItem(self._make_item(entry))
            self.list.scrollToBottom()
        self._update_count()

    def log_run_start(self, total: int):
        self.log("system", "─" * 38)
        self.log("system", f"▶ Iniciado — {total} bloco(s)  •  {datetime.now().strftime('%d/%m %H:%M:%S')}")

    def log_run_end(self, ok: int, total: int):
        icon = "✅" if ok == total else "⚠️"
        self.log("system", f"{icon} Encerrado — {ok}/{total} com sucesso")
        self.log("system", "─" * 38)

    def clear(self):
        self._entries.clear()
        self.list.clear()
        self._update_count()

    # ── Filtros ───────────────────────────────────────────────────────

    def _on_filter(self, level):
        self._active_filter = level
        for key, btn in self._filter_btns.items():
            btn.setChecked(key == str(level))
        self._rebuild_list()

    def _on_search(self, text: str):
        self._search_text = text.lower()
        self._rebuild_list()

    def _matches(self, entry: LogEntry) -> bool:
        if self._active_filter and entry.level != self._active_filter:
            return False
        if self._search_text and self._search_text not in entry.message.lower():
            return False
        return True

    def _rebuild_list(self):
        self.list.clear()
        for entry in self._entries:
            if self._matches(entry):
                self.list.addItem(self._make_item(entry))
        self.list.scrollToBottom()
        self._update_count()

    def _make_item(self, entry: LogEntry) -> QListWidgetItem:
        cfg  = LOG_TYPES.get(entry.level, LOG_TYPES["info"])
        text = f"  {cfg['icon']}  {entry.timestamp}  {entry.message}"
        item = QListWidgetItem(text)
        item.setForeground(QColor(cfg["color"]))
        item.setBackground(QColor(cfg["bg"]))
        item.setSizeHint(QSize(0, 21))
        item.setFont(QFont("Consolas", 10))
        return item

    def _update_count(self):
        visible = self.list.count()
        total   = len(self._entries)
        self.lbl_count.setText(
            f"{total}" if visible == total else f"{visible}/{total}"
        )

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_copy(self):
        lines = [self.list.item(i).text().strip()
                 for i in range(self.list.count())]
        if lines:
            QApplication.clipboard().setText("\n".join(lines))

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar log",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Texto (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("PyFlow RPA — Log de execução\n")
            f.write(f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            for entry in self._entries:
                f.write(entry.to_text() + "\n")

    # ── Estilos ───────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            #log_panel, #log_header { background-color: #181825; }
            #log_title { font-size: 12px; font-weight: 600; color: #6c7086; }
            #log_sep   { color: #313244; }
            #log_count { font-size: 10px; color: #45475a; font-family: monospace; min-width: 28px; }

            #log_filter_btn {
                background-color: #313244; color: #6c7086;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 0 7px; font-size: 10px; font-weight: 600;
            }
            #log_filter_btn:hover  { background-color: #45475a; color: #cdd6f4; }
            #log_filter_btn:checked { background-color: #45475a; color: #cdd6f4; border-color: #cba6f7; }

            #log_search {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 4px; padding: 1px 8px;
                color: #cdd6f4; font-size: 11px;
            }
            #log_search:focus { border-color: #cba6f7; }

            #log_action_btn {
                background-color: #313244; color: #a6adc8;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 0 8px; font-size: 11px;
            }
            #log_action_btn:hover { background-color: #45475a; color: #cdd6f4; }

            #log_clear_btn {
                background-color: transparent; color: #45475a;
                border: none; font-size: 13px; border-radius: 4px;
                padding: 0 6px;
            }
            #log_clear_btn:hover { color: #f38ba8; background-color: #3a1c1c; }

            #log_list {
                background-color: #11111b; border: none;
                font-family: 'Consolas', monospace; font-size: 11px;
            }
            #log_list::item { padding: 0 4px; border: none; }
            #log_list::item:selected { background-color: #313244; }

            QScrollBar:vertical { background: #1e1e2e; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)