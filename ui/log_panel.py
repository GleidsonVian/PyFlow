"""
Log panel ultra-moderno do PyFlow RPA.
— Design de Console Unificado (estilo IDE/Terminal)
— Layout de linha única de alta densidade
— Filtros integrados no header
Coloque em: ui/log_panel.py
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QLineEdit, QFrame,
    QFileDialog, QApplication, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont


# ── Cores por nível de log ────────────────────────────────────────────────────

LOG_TYPES = {
    "info":    {"color": "#89b4fa", "bg": "#1a2a40", "icon": "ℹ",  "dim": "#45475a"},
    "running": {"color": "#cba6f7", "bg": "#221838", "icon": "▶",  "dim": "#585b70"},
    "success": {"color": "#a6e3a1", "bg": "#182e20", "icon": "✓",  "dim": "#45475a"},
    "error":   {"color": "#f38ba8", "bg": "#2e1818", "icon": "✗",  "dim": "#903050"},
    "warning": {"color": "#fab387", "bg": "#2e2010", "icon": "⚠",  "dim": "#906030"},
    "system":  {"color": "#6c7086", "bg": "#1e1e2e", "icon": "⚙",  "dim": "#45475a"},
}

# ── Cores e ícones por categoria de bloco ────────────────────────────────────

CATEGORY_META = {
    "Navegador":  {"color": "#89b4fa", "bg": "#1a2a44", "short": "NAV", "icon": "🌐"},
    "Controle":   {"color": "#cba6f7", "bg": "#221840", "short": "CTL", "icon": "🔧"},
    "Arquivos":   {"color": "#a6e3a1", "bg": "#182e22", "short": "ARQ", "icon": "📁"},
    "Integração": {"color": "#fab387", "bg": "#2e2014", "short": "INT", "icon": "🔌"},
    "Sistema":    {"color": "#f38ba8", "bg": "#2e1820", "short": "SIS", "icon": "💻"},
    "Gatilhos":    {"color": "#f9e2af", "bg": "#2e2a18", "short": "GAT", "icon": "⚡"},
}

FILTER_LEVELS = [
    ("Todos",  None),
    ("Erros", "error"),
    ("Avisos", "warning"),
    ("Logs",   "info"),
]


# ── Estrutura de entrada de log ───────────────────────────────────────────────

class LogEntry:
    def __init__(self, level: str, message: str, timestamp: str,
                 step: int = 0, block_name: str = "", category: str = ""):
        self.level      = level
        self.message    = message
        self.timestamp  = timestamp
        self.step       = step
        self.block_name = block_name
        self.category   = category

    def to_text(self) -> str:
        cat = f"[{self.category}] " if self.category else ""
        blk = f"[{self.block_name}] " if self.block_name else ""
        return f"[{self.timestamp}] [{self.level.upper():7}] {cat}{blk}{self.message}"


# ── Widget de linha de log (Style: Console Row) ───────────────────────────────

class LogRow(QWidget):
    def __init__(self, entry: LogEntry, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._build()

    def _build(self):
        e   = self._entry
        lvl = LOG_TYPES.get(e.level, LOG_TYPES["info"])
        cat = CATEGORY_META.get(e.category) if e.category else None

        self.setFixedHeight(24)
        self.setObjectName("log_row")

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 0, 12, 0)
        root.setSpacing(10)

        # 1. Timestamp
        ts_lbl = QLabel(e.timestamp)
        ts_lbl.setFixedWidth(52)
        ts_lbl.setStyleSheet(f"color: {lvl['dim']}; font-size: 10px; font-family: 'Consolas', monospace;")
        root.addWidget(ts_lbl)

        # 2. Ícone
        icon_lbl = QLabel(lvl["icon"])
        icon_lbl.setFixedWidth(12)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"color: {lvl['color']}; font-size: 11px;")
        root.addWidget(icon_lbl)

        # 3. Badge Categoria
        if cat:
            badge = QLabel(cat['short'])
            badge.setFixedWidth(30)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                f"background: {cat['bg']}; color: {cat['color']};"
                f"border-radius: 2px; font-size: 8px; font-weight: 900; padding: 1px 0;"
            )
            root.addWidget(badge)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(30)
            root.addWidget(spacer)

        # 4. Mensagem
        msg_text = e.message
        if e.block_name:
            msg_text = f"<span style='color: {lvl['color']}; font-weight: 600;'>{e.block_name}</span> &nbsp; {e.message}"
        
        msg_lbl = QLabel(msg_text)
        msg_lbl.setStyleSheet(f"color: #cdd6f4; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        msg_lbl.setWordWrap(False)
        root.addWidget(msg_lbl, 1)

        # Estilo de hover e borda sutil
        self.setStyleSheet(f"#log_row {{ border-bottom: 1px solid #18182520; background-color: {lvl['bg']}05; }}")

    def entry_text(self) -> str:
        return self._entry.to_text()


# ── Painel de log (Style: Unified Console) ───────────────────────────────────

class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
        self.setMinimumHeight(60)
        self._entries: list[LogEntry] = []
        self._active_level    = None
        self._search_text     = ""
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("log_header")
        header.setFixedHeight(32)
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 0, 8, 0)
        h.setSpacing(10)

        lbl = QLabel("CONSOLE")
        lbl.setStyleSheet("color: #585b70; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        h.addWidget(lbl)

        h.addSpacing(15)

        self._level_btns: dict[str, QPushButton] = {}
        for label, level in FILTER_LEVELS:
            btn = QPushButton(label)
            btn.setObjectName("log_tab_btn")
            btn.setCheckable(True)
            btn.setChecked(level is None)
            btn.clicked.connect(lambda _, lv=level: self._on_level_filter(lv))
            self._level_btns[str(level)] = btn
            h.addWidget(btn)

        h.addStretch()

        self.search = QLineEdit()
        self.search.setObjectName("log_search")
        self.search.setPlaceholderText("Filtrar...")
        self.search.setFixedWidth(130)
        self.search.setFixedHeight(20)
        self.search.textChanged.connect(self._on_search)
        h.addWidget(self.search)

        # Ações
        for text, tip, slot in [
            ("⎘", "Copiar logs", self._on_copy),
            ("🗑", "Limpar console", self.clear),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("log_tool_btn")
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        root.addWidget(header)

        # Conteúdo
        self.scroll = QScrollArea()
        self.scroll.setObjectName("log_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
        self._content.setObjectName("log_content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.setAlignment(Qt.AlignTop)

        # Label de "vazio" (fora do layout de conteúdo para não ser deletado no clear)
        self._empty_lbl = QLabel("Aguardando execução...")
        self._empty_lbl.setObjectName("log_empty")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self._empty_lbl)

        self.scroll.setWidget(self._content)
        root.addWidget(self.scroll, 1)

    def log(self, level: str, message: str,
            step: int = 0, block_name: str = "", category: str = ""):
        ts    = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(level, message, ts,
                         step=step, block_name=block_name, category=category)
        self._entries.append(entry)
        if self._matches(entry):
            self._append_row(entry)

    def log_run_start(self, total: int):
        self.log("system", "─" * 50)
        self.log("system", f"▶ INICIADO — {total} passos")

    def log_run_end(self, ok: int, total: int):
        icon = "✅" if ok == total else "⚠️"
        self.log("system", f"{icon} CONCLUÍDO — {ok}/{total} sucesso")
        self.log("system", "─" * 50)

    def clear(self):
        self._entries.clear()
        self._rebuild_list()

    def _on_level_filter(self, level):
        self._active_level = level
        for key, btn in self._level_btns.items():
            btn.setChecked(key == str(level))
        self._rebuild_list()

    def _on_search(self, text: str):
        self._search_text = text.lower()
        self._rebuild_list()

    def _matches(self, entry: LogEntry) -> bool:
        if self._active_level and entry.level != self._active_level:
            return False
        if self._search_text:
            haystack = (entry.message + entry.block_name).lower()
            if self._search_text not in haystack:
                return False
        return True

    def _append_row(self, entry: LogEntry):
        if self._empty_lbl.isVisible():
            self._empty_lbl.hide()
        row = LogRow(entry)
        self._content_layout.addWidget(row)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _rebuild_list(self):
        # Limpa widgets do layout de conteúdo
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()

        filtered = [e for e in self._entries if self._matches(e)]
        
        if not filtered:
            self._empty_lbl.show()
            self._empty_lbl.setText("Sem resultados para o filtro." if self._search_text or self._active_level else "Aguardando execução...")
        else:
            self._empty_lbl.hide()
            for entry in filtered:
                self._content_layout.addWidget(LogRow(entry))
            self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _on_copy(self):
        lines = [e.to_text() for e in self._entries if self._matches(e)]
        if lines: QApplication.clipboard().setText("\n".join(lines))

    def _apply_styles(self):
        self.setStyleSheet("""
            #log_panel { background-color: #0b0b10; border-top: 1px solid #181825; }
            #log_header { background-color: #11111b; }
            
            #log_tab_btn {
                background: transparent; color: #585b70; border: none;
                font-size: 11px; font-weight: 700; padding: 0 8px;
                border-bottom: 2px solid transparent;
            }
            #log_tab_btn:hover { color: #cdd6f4; }
            #log_tab_btn:checked { color: #cba6f7; border-bottom: 2px solid #cba6f7; }

            #log_search {
                background: #181825; color: #cdd6f4; border: 1px solid #313244;
                border-radius: 3px; padding: 0 8px; font-size: 10px;
            }
            #log_search:focus { border-color: #45475a; }

            #log_tool_btn {
                background: transparent; color: #45475a; border: none;
                font-size: 13px; padding: 2px 6px; border-radius: 3px;
            }
            #log_tool_btn:hover { background: #313244; color: #f38ba8; }

            #log_scroll, #log_content { background: #0b0b10; border: none; }
            #log_empty { color: #313244; font-size: 11px; padding: 20px; font-style: italic; }
            
            QScrollBar:vertical {
                background: #0b0b10; width: 4px;
            }
            QScrollBar::handle:vertical {
                background: #313244; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
