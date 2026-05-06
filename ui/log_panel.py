"""
Log panel melhorado do PyFlow RPA.
— Itens com duas linhas: badge de categoria + nome do bloco / mensagem
— Filtro por tipo (OK, Erro, Exec, Info, Sist) E por categoria de bloco
— Busca por texto, copiar log visível, exportar TXT
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
    "info":    {"color": "#89b4fa", "bg": "#1a2a40", "icon": "ℹ",  "dim": "#4a6a90"},
    "running": {"color": "#cba6f7", "bg": "#221838", "icon": "▶",  "dim": "#6a4a90"},
    "success": {"color": "#a6e3a1", "bg": "#182e20", "icon": "✓",  "dim": "#4a8a60"},
    "error":   {"color": "#f38ba8", "bg": "#2e1818", "icon": "✗",  "dim": "#903050"},
    "warning": {"color": "#fab387", "bg": "#2e2010", "icon": "⚠",  "dim": "#906030"},
    "system":  {"color": "#6c7086", "bg": "#1e1e2e", "icon": "⚙",  "dim": "#404050"},
}

# ── Cores e ícones por categoria de bloco ────────────────────────────────────

CATEGORY_META = {
    "Navegador":  {"color": "#89b4fa", "bg": "#1a2a44", "short": "NAV", "icon": "🌐"},
    "Controle":   {"color": "#cba6f7", "bg": "#221840", "short": "CTL", "icon": "🔧"},
    "Arquivos":   {"color": "#a6e3a1", "bg": "#182e22", "short": "ARQ", "icon": "📁"},
    "Integração": {"color": "#fab387", "bg": "#2e2014", "short": "INT", "icon": "🔌"},
    "Sistema":    {"color": "#f38ba8", "bg": "#2e1820", "short": "SIS", "icon": "💻"},
}

FILTER_LEVELS = [
    ("Todos",  None),
    ("✓ OK",   "success"),
    ("✗ Erro", "error"),
    ("▶ Exec", "running"),
    ("ℹ Info", "info"),
    ("⚙ Sist", "system"),
]

FILTER_CATEGORIES = [c for c in CATEGORY_META]  # lista de categorias para filtro


# ── Estrutura de entrada de log ───────────────────────────────────────────────

class LogEntry:
    def __init__(self, level: str, message: str, timestamp: str,
                 step: int = 0, block_name: str = "", category: str = ""):
        self.level      = level
        self.message    = message
        self.timestamp  = timestamp
        self.step       = step          # número do passo (0 = entrada de sistema)
        self.block_name = block_name    # nome legível do bloco
        self.category   = category      # "Navegador", "Controle", etc.

    def to_text(self) -> str:
        cat = f"[{self.category}] " if self.category else ""
        blk = f"[{self.block_name}] " if self.block_name else ""
        return f"[{self.timestamp}] [{self.level.upper():7}] {cat}{blk}{self.message}"


# ── Widget de linha de log ────────────────────────────────────────────────────

class LogRow(QWidget):
    """
    Uma linha do log com layout de duas colunas:
    Esquerda: ícone de nível  |  Direita: badge categoria + nome bloco / mensagem
    """
    HEIGHT_WITH_BLOCK = 42
    HEIGHT_SIMPLE     = 24

    def __init__(self, entry: LogEntry, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._build()

    def _build(self):
        e   = self._entry
        lvl = LOG_TYPES.get(e.level, LOG_TYPES["info"])
        cat = CATEGORY_META.get(e.category) if e.category else None

        has_block = bool(e.block_name and e.category)
        self.setFixedHeight(self.HEIGHT_WITH_BLOCK if has_block else self.HEIGHT_SIMPLE)

        # Fundo baseado no nível
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(lvl["bg"]))
        self.setPalette(pal)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 4, 10, 4)
        root.setSpacing(8)

        # ── Coluna esquerda: ícone nível + hora ───────────────────────
        left = QVBoxLayout()
        left.setSpacing(0)
        left.setContentsMargins(0, 0, 0, 0)
        left.setAlignment(Qt.AlignTop)

        icon_lbl = QLabel(lvl["icon"])
        icon_lbl.setFixedWidth(16)
        icon_lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        icon_lbl.setStyleSheet(f"color: {lvl['color']}; font-size: 12px;")
        left.addWidget(icon_lbl)

        ts_lbl = QLabel(e.timestamp)
        ts_lbl.setStyleSheet(f"color: {lvl['dim']}; font-size: 9px; font-family: Consolas;")
        ts_lbl.setAlignment(Qt.AlignHCenter)
        left.addWidget(ts_lbl)

        root.addLayout(left)

        # Separador vertical
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"color: {lvl['dim']};")
        root.addWidget(sep)

        # ── Coluna direita: conteúdo ──────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(2)
        right.setContentsMargins(0, 2, 0, 2)
        right.setAlignment(Qt.AlignTop)

        if has_block:
            # Linha 1: badge de categoria + nome do bloco
            top_row = QHBoxLayout()
            top_row.setSpacing(6)
            top_row.setContentsMargins(0, 0, 0, 0)

            # Badge de categoria
            badge = QLabel(f"{cat['icon']} {cat['short']}")
            badge.setFixedHeight(16)
            badge.setStyleSheet(
                f"background: {cat['bg']}; color: {cat['color']};"
                f"border-radius: 3px; padding: 0 5px;"
                f"font-size: 9px; font-weight: 700; font-family: Consolas;"
            )
            top_row.addWidget(badge)

            # Número do passo
            if e.step:
                step_lbl = QLabel(f"#{e.step}")
                step_lbl.setFixedHeight(16)
                step_lbl.setStyleSheet(
                    f"color: {lvl['dim']}; font-size: 9px; font-family: Consolas;"
                )
                top_row.addWidget(step_lbl)

            # Nome do bloco
            name_lbl = QLabel(e.block_name)
            name_lbl.setStyleSheet(
                f"color: {lvl['color']}; font-size: 11px; font-weight: 600; font-family: Consolas;"
            )
            top_row.addWidget(name_lbl)
            top_row.addStretch()
            right.addLayout(top_row)

            # Linha 2: mensagem
            msg_lbl = QLabel(e.message)
            msg_lbl.setStyleSheet(
                f"color: #a6adc8; font-size: 10px; font-family: Consolas;"
            )
            msg_lbl.setWordWrap(False)
            right.addWidget(msg_lbl)

        else:
            # Linha simples: só a mensagem (entradas de sistema, info, etc.)
            msg_lbl = QLabel(e.message)
            msg_lbl.setStyleSheet(
                f"color: {lvl['color']}; font-size: 11px; font-family: Consolas;"
            )
            msg_lbl.setWordWrap(False)
            msg_lbl.setAlignment(Qt.AlignVCenter)
            right.addWidget(msg_lbl)

        root.addLayout(right, 1)

    def entry_text(self) -> str:
        return self._entry.to_text()


# ── Painel de log ─────────────────────────────────────────────────────────────

class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
<<<<<<< HEAD
        self.setMinimumHeight(80)
=======
        self.setFixedHeight(200)
>>>>>>> 23424c6 (commit)
        self._entries: list[LogEntry] = []
        self._active_level    = None   # filtro de nível
        self._active_category = None   # filtro de categoria
        self._search_text     = ""
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header: título + filtros de nível ────────────────────────
        header = QWidget()
        header.setObjectName("log_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(10, 5, 8, 5)
        h.setSpacing(4)

        lbl = QLabel("📋  Log")
        lbl.setObjectName("log_title")
        h.addWidget(lbl)

        # Filtros por nível
        self._level_btns: dict[str, QPushButton] = {}
        for label, level in FILTER_LEVELS:
            btn = QPushButton(label)
            btn.setObjectName("log_filter_btn")
            btn.setCheckable(True)
            btn.setChecked(level is None)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda _, lv=level: self._on_level_filter(lv))
            self._level_btns[str(level)] = btn
            h.addWidget(btn)

        h.addStretch()

        # Busca
        self.search = QLineEdit()
        self.search.setObjectName("log_search")
        self.search.setPlaceholderText("🔍 Buscar...")
        self.search.setFixedWidth(140)
        self.search.setFixedHeight(22)
        self.search.textChanged.connect(self._on_search)
        h.addWidget(self.search)

        # Contador
        self.lbl_count = QLabel("0")
        self.lbl_count.setObjectName("log_count")
        h.addWidget(self.lbl_count)

        # Botões de ação
        for text, tip, slot in [
            ("⎘ Copiar",    "Copiar log visível para área de transferência", self._on_copy),
            ("💾 Exportar", "Exportar log completo como .txt",               self._on_export),
            ("🗑",           "Limpar todo o log",                            self.clear),
        ]:
            btn = QPushButton(text)
            obj = "log_action_btn" if len(text) > 2 else "log_clear_btn"
            btn.setObjectName(obj)
            btn.setFixedHeight(22)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        root.addWidget(header)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.HLine); sep1.setObjectName("log_sep")
        root.addWidget(sep1)

        # ── Sub-header: filtros por categoria ────────────────────────
        cat_bar = QWidget()
        cat_bar.setObjectName("log_cat_bar")
        c = QHBoxLayout(cat_bar)
        c.setContentsMargins(10, 3, 8, 3)
        c.setSpacing(4)

        lbl_cat = QLabel("Categoria:")
        lbl_cat.setObjectName("log_cat_label")
        c.addWidget(lbl_cat)

        self._cat_btns: dict[str, QPushButton] = {}

        # Botão "Todas"
        btn_all = QPushButton("Todas")
        btn_all.setObjectName("log_cat_btn")
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        btn_all.setFixedHeight(20)
        btn_all.clicked.connect(lambda _: self._on_cat_filter(None))
        self._cat_btns["None"] = btn_all
        c.addWidget(btn_all)

        for cat_name, meta in CATEGORY_META.items():
            btn = QPushButton(f"{meta['icon']} {cat_name}")
            btn.setObjectName("log_cat_btn")
            btn.setProperty("cat_color", meta["color"])
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setFixedHeight(20)
            btn.clicked.connect(lambda _, cn=cat_name: self._on_cat_filter(cn))
            self._cat_btns[cat_name] = btn
            c.addWidget(btn)

        c.addStretch()
        root.addWidget(cat_bar)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setObjectName("log_sep")
        root.addWidget(sep2)

        # ── Área de scroll com as linhas de log ──────────────────────
        self.scroll = QScrollArea()
        self.scroll.setObjectName("log_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setObjectName("log_content")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(1)
        self._content_layout.setAlignment(Qt.AlignTop)

        self._empty_lbl = QLabel("Nenhuma entrada no log ainda.")
        self._empty_lbl.setObjectName("log_empty")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(self._empty_lbl)

        self.scroll.setWidget(self._content)
        root.addWidget(self.scroll, 1)

    # ── API pública ───────────────────────────────────────────────────

    def log(self, level: str, message: str,
            step: int = 0, block_name: str = "", category: str = ""):
        ts    = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(level, message, ts,
                         step=step, block_name=block_name, category=category)
        self._entries.append(entry)
        if self._matches(entry):
            self._append_row(entry)
        self._update_count()

    def log_run_start(self, total: int):
        self.log("system", "─" * 46)
        self.log("system", f"▶  Iniciado — {total} bloco(s)  •  {datetime.now().strftime('%d/%m %H:%M:%S')}")

    def log_run_end(self, ok: int, total: int):
        icon = "✅" if ok == total else "⚠️"
        self.log("system", f"{icon}  Encerrado — {ok}/{total} com sucesso")
        self.log("system", "─" * 46)

    def clear(self):
        self._entries.clear()
        self._rebuild_list()

    # ── Filtros ───────────────────────────────────────────────────────

    def _on_level_filter(self, level):
        self._active_level = level
        for key, btn in self._level_btns.items():
            btn.setChecked(key == str(level))
        self._rebuild_list()

    def _on_cat_filter(self, category):
        self._active_category = category
        for key, btn in self._cat_btns.items():
            btn.setChecked(key == str(category))
        self._rebuild_list()

    def _on_search(self, text: str):
        self._search_text = text.lower()
        self._rebuild_list()

    def _matches(self, entry: LogEntry) -> bool:
        if self._active_level and entry.level != self._active_level:
            return False
        if self._active_category and entry.category != self._active_category:
            return False
        if self._search_text:
            haystack = (entry.message + entry.block_name + entry.category).lower()
            if self._search_text not in haystack:
                return False
        return True

    # ── Renderização ─────────────────────────────────────────────────

    def _append_row(self, entry: LogEntry):
        # Remove o label "vazio" se ainda estiver lá
        if self._empty_lbl.isVisible():
            self._empty_lbl.hide()
        row = LogRow(entry)
        self._content_layout.addWidget(row)
        # Scroll para o fim
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _rebuild_list(self):
        # Remove todos os widgets do layout
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = [e for e in self._entries if self._matches(e)]

        if not filtered:
            lbl = QLabel(
                "Nenhum resultado para este filtro."
                if (self._active_level or self._active_category or self._search_text)
                else "Nenhuma entrada no log ainda."
            )
            lbl.setObjectName("log_empty")
            lbl.setAlignment(Qt.AlignCenter)
            self._empty_lbl = lbl
            self._content_layout.addWidget(lbl)
        else:
            self._empty_lbl = QLabel()   # placeholder inativo
            for entry in filtered:
                row = LogRow(entry)
                self._content_layout.addWidget(row)
            self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            )

        self._update_count()

    def _update_count(self):
        visible = sum(1 for e in self._entries if self._matches(e))
        total   = len(self._entries)
        self.lbl_count.setText(
            f"{total}" if visible == total else f"{visible}/{total}"
        )

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_copy(self):
        lines = []
        for i in range(self._content_layout.count()):
            w = self._content_layout.itemAt(i).widget()
            if isinstance(w, LogRow):
                lines.append(w.entry_text())
        if lines:
            QApplication.clipboard().setText("\n".join(lines))

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar log",
            f"pyflow_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
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
            #log_panel   { background-color: #181825; }
            #log_header  { background-color: #181825; }
            #log_cat_bar { background-color: #11111b; }
            #log_title   { font-size: 12px; font-weight: 600; color: #6c7086; padding-right: 4px; }
            #log_sep     { color: #313244; max-height: 1px; }
            #log_count   {
                font-size: 10px; color: #45475a; font-family: Consolas;
                min-width: 36px; text-align: right;
            }
            #log_cat_label {
                font-size: 10px; color: #45475a; margin-right: 2px;
            }

            #log_filter_btn {
                background-color: #313244; color: #6c7086;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 0 7px; font-size: 10px; font-weight: 600;
            }
            #log_filter_btn:hover   { background-color: #45475a; color: #cdd6f4; }
            #log_filter_btn:checked { background-color: #45475a; color: #cdd6f4; border-color: #cba6f7; }

            #log_cat_btn {
                background-color: #1e1e2e; color: #585b70;
                border: 1px solid #313244; border-radius: 4px;
                padding: 0 6px; font-size: 10px;
            }
            #log_cat_btn:hover   { background-color: #313244; color: #cdd6f4; }
            #log_cat_btn:checked { background-color: #313244; color: #cdd6f4; border-color: #89b4fa; }

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
                border: none; font-size: 13px; border-radius: 4px; padding: 0 6px;
            }
            #log_clear_btn:hover { color: #f38ba8; background-color: #3a1c1c; }

            #log_scroll, #log_content { background-color: #11111b; border: none; }
            #log_empty {
                color: #45475a; font-size: 11px; padding: 16px;
                font-family: Consolas;
            }

            QScrollBar:vertical {
                background: #1e1e2e; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #45475a; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
