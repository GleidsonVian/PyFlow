"""
Painel de variáveis ao vivo do PyFlow RPA.
Exibe todas as variáveis do contexto em tempo real durante/após execução.
Coloque em: ui/variables_panel.py
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QPushButton, QLineEdit,
    QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont


class VariableRow(QWidget):
    """Uma linha da tabela de variáveis."""

    def __init__(self, name: str, value, parent=None):
        super().__init__(parent)
        self.setObjectName("var_row")
        self._name  = name
        self._value = value
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # Tipo
        tipo = self._get_type_badge()
        lbl_type = QLabel(tipo["label"])
        lbl_type.setObjectName(f"var_type_{tipo['id']}")
        lbl_type.setFixedWidth(40)
        lbl_type.setAlignment(Qt.AlignCenter)

        # Nome
        lbl_name = QLabel(self._name)
        lbl_name.setObjectName("var_name")
        lbl_name.setFixedWidth(130)
        lbl_name.setToolTip(self._name)

        # Valor
        val_str = self._format_value()
        lbl_val = QLabel(val_str)
        lbl_val.setObjectName("var_value")
        lbl_val.setToolTip(str(self._value))
        lbl_val.setWordWrap(False)

        # Botão copiar
        btn_copy = QLabel("⎘")
        btn_copy.setObjectName("var_copy")
        btn_copy.setFixedSize(20, 20)
        btn_copy.setAlignment(Qt.AlignCenter)
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setToolTip("Copiar valor")
        btn_copy.mousePressEvent = lambda e: self._copy_value()

        layout.addWidget(lbl_type)
        layout.addWidget(lbl_name)
        layout.addWidget(lbl_val, 1)
        layout.addWidget(btn_copy)

    def _get_type_badge(self) -> dict:
        v = self._value
        if isinstance(v, list):
            return {"label": "[ ]", "id": "list"}
        elif isinstance(v, bool):
            return {"label": "bool", "id": "bool"}
        elif isinstance(v, int):
            return {"label": "int", "id": "int"}
        elif isinstance(v, float):
            return {"label": "float", "id": "float"}
        else:
            s = str(v)
            if s.isdigit():
                return {"label": "num", "id": "num"}
            return {"label": "str", "id": "str"}

    def _format_value(self) -> str:
        v = self._value
        if isinstance(v, list):
            count = len(v)
            preview = ", ".join(str(i)[:20] for i in v[:3])
            suffix = f" +{count - 3}" if count > 3 else ""
            return f"[{preview}{suffix}]  ({count} itens)"
        s = str(v)
        if len(s) > 60:
            return s[:57] + "..."
        return s

    def _copy_value(self):
        v = self._value
        text = ", ".join(str(i) for i in v) if isinstance(v, list) else str(v)
        QApplication.clipboard().setText(text)


class VariablesPanel(QWidget):
    """Painel lateral de variáveis ao vivo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("vars_panel")
        self._filter_text = ""
        self._build_ui()
        self._apply_styles()

        # Timer para atualizar em tempo real
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.setInterval(500)  # atualiza a cada 500ms

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("vars_header")
        h = QVBoxLayout(header)
        h.setContentsMargins(12, 10, 12, 8)
        h.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("⚡ Variáveis")
        title.setObjectName("vars_title")

        self.lbl_count = QLabel("0 variáveis")
        self.lbl_count.setObjectName("vars_count")

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.lbl_count)
        h.addLayout(title_row)

        # Busca
        self.search = QLineEdit()
        self.search.setObjectName("vars_search")
        self.search.setPlaceholderText("🔍  Filtrar variáveis...")
        self.search.textChanged.connect(self._on_filter)
        h.addWidget(self.search)

        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("vars_sep")
        root.addWidget(sep)

        # ── Legenda de tipos ──────────────────────────────────────────
        legend = QWidget()
        legend.setObjectName("vars_legend")
        leg_layout = QHBoxLayout(legend)
        leg_layout.setContentsMargins(10, 4, 10, 4)
        leg_layout.setSpacing(10)

        for label, obj_id in [("str", "str"), ("[ ]", "list"), ("num", "num"), ("bool", "bool")]:
            lbl = QLabel(label)
            lbl.setObjectName(f"var_type_{obj_id}")
            lbl.setFixedWidth(32)
            lbl.setAlignment(Qt.AlignCenter)
            leg_layout.addWidget(lbl)

        leg_layout.addStretch()
        root.addWidget(legend)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("vars_sep")
        root.addWidget(sep2)

        # ── Scroll de variáveis ───────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("vars_scroll")
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content.setObjectName("vars_content")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(2)
        self.content_layout.setAlignment(Qt.AlignTop)

        self._empty_label = QLabel("Nenhuma variável ainda.\nExecute um fluxo para\nver os valores aqui.")
        self._empty_label.setObjectName("vars_empty")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self._empty_label)

        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setObjectName("vars_sep")
        root.addWidget(sep3)

        # ── Footer ────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("vars_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(10, 6, 10, 6)
        f.setSpacing(8)

        btn_refresh = QPushButton("↻  Atualizar")
        btn_refresh.setObjectName("btn_vars_refresh")
        btn_refresh.clicked.connect(self.refresh)

        btn_clear = QPushButton("Limpar")
        btn_clear.setObjectName("btn_vars_clear")
        btn_clear.clicked.connect(self.clear_context)

        f.addWidget(btn_refresh)
        f.addStretch()
        f.addWidget(btn_clear)
        root.addWidget(footer)

    def start_live(self):
        """Inicia atualização em tempo real."""
        self._timer.start()

    def stop_live(self):
        """Para atualização em tempo real e faz refresh final."""
        self._timer.stop()
        self.refresh()

    def refresh(self):
        """Atualiza o painel com os valores atuais do contexto."""
        context = self._get_context()
        self._render(context)

    def _get_context(self) -> dict:
        try:
            from blocks.browser.extract_text import ExtractTextBlock
            return dict(ExtractTextBlock._context)
        except Exception:
            return {}

    def clear_context(self):
        try:
            from blocks.browser.extract_text import ExtractTextBlock
            ExtractTextBlock._context.clear()
            self.refresh()
        except Exception:
            pass

    def _on_filter(self, text: str):
        self._filter_text = text.lower()
        self.refresh()

    def _render(self, context: dict):
        # Limpa o layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filtra por texto de busca
        filtered = {
            k: v for k, v in context.items()
            if self._filter_text in k.lower() or
               self._filter_text in str(v).lower()
        } if self._filter_text else context

        count = len(filtered)
        self.lbl_count.setText(f"{count} variável" if count == 1 else f"{count} variáveis")

        if not filtered:
            empty_text = (
                "Nenhuma variável encontrada."
                if self._filter_text else
                "Nenhuma variável ainda.\nExecute um fluxo para\nver os valores aqui."
            )
            lbl = QLabel(empty_text)
            lbl.setObjectName("vars_empty")
            lbl.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        # Separa variáveis por tipo para ordenar
        lists   = {k: v for k, v in filtered.items() if isinstance(v, list)}
        strings = {k: v for k, v in filtered.items() if not isinstance(v, list)}

        # Renderiza strings primeiro, listas depois
        first = True
        for name, value in {**strings, **lists}.items():
            if not first:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setObjectName("vars_row_sep")
                self.content_layout.addWidget(sep)
            row = VariableRow(name, value)
            self.content_layout.addWidget(row)
            first = False

        self.content_layout.addStretch()

    def _apply_styles(self):
        self.setStyleSheet("""
            #vars_panel { background-color: #181825; }
            #vars_header { background-color: #181825; }
            #vars_title { font-size: 13px; font-weight: 700; color: #cba6f7; }
            #vars_count { font-size: 11px; color: #45475a; }
            #vars_search {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 8px;
                color: #cdd6f4; font-size: 11px;
            }
            #vars_search:focus { border-color: #cba6f7; }
            #vars_sep, #vars_row_sep { color: #313244; }
            #vars_legend { background-color: #11111b; }
            #vars_scroll, #vars_content { background-color: #181825; border: none; }
            #vars_empty { color: #45475a; font-size: 11px; padding: 20px; }
            #vars_footer { background-color: #181825; }

            #var_row { background-color: #1e1e2e; }
            #var_row:hover { background-color: #252535; }

            #var_name {
                font-size: 11px; font-weight: 600; color: #cdd6f4;
                font-family: monospace;
            }
            #var_value {
                font-size: 11px; color: #a6adc8; font-family: monospace;
            }
            #var_copy {
                color: #45475a; font-size: 13px; border-radius: 4px;
            }
            #var_copy:hover { color: #cba6f7; }

            /* Badges de tipo */
            #var_type_str {
                background-color: #1e3a5f; color: #89b4fa;
                border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 1px 3px;
            }
            #var_type_list {
                background-color: #2a1e3f; color: #cba6f7;
                border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 1px 3px;
            }
            #var_type_num, #var_type_int, #var_type_float {
                background-color: #1e3a2a; color: #a6e3a1;
                border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 1px 3px;
            }
            #var_type_bool {
                background-color: #3a2a1c; color: #fab387;
                border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 1px 3px;
            }

            #btn_vars_refresh {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 5px 10px; font-size: 11px;
            }
            #btn_vars_refresh:hover { background-color: #45475a; }
            #btn_vars_clear {
                background-color: transparent; color: #45475a; border: none;
                font-size: 11px; text-decoration: underline;
            }
            #btn_vars_clear:hover { color: #f38ba8; }
        """)
