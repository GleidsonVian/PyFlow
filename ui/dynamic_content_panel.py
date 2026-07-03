"""
Painel flutuante de Conteúdo Dinâmico — inspirado no Power Automate.
Aparece ao focar em campos de texto e lista todas as variáveis/saídas
de nós anteriores. Clique num item insere {{var_name}} no campo ativo.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QWidget, QPushButton, QApplication, QToolTip
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QCursor


class DynamicContentPanel(QFrame):
    """
    Popup flutuante de conteúdo dinâmico.

    Uso:
        panel = DynamicContentPanel()
        panel.variable_selected.connect(lambda tok: field.insert(tok))
        panel.show_for(field, context_vars, nodes_data)
    """

    variable_selected = Signal(str)   # emite "{{var_name}}"

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setObjectName("dyn_panel")
        self.setFixedWidth(330)
        self.setMaximumHeight(420)

        self._target_field = None
        self._all_rows: list[tuple[QWidget, str, str]] = []

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(180)
        self._hide_timer.timeout.connect(self.hide)

        self._build_ui()
        self._apply_styles()
        self.hide()

    # ── construção da UI ─────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Cabeçalho
        hdr = QWidget()
        hdr.setObjectName("dyn_header")
        h = QHBoxLayout(hdr)
        h.setContentsMargins(12, 8, 8, 8)
        h.setSpacing(6)
        title = QLabel("⚡  Conteúdo Dinâmico")
        title.setObjectName("dyn_title")
        h.addWidget(title, 1)

        self._btn_copy_all = QPushButton("📋 Copiar tudo")
        self._btn_copy_all.setObjectName("dyn_copy_all")
        self._btn_copy_all.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_copy_all.setToolTip("Copia todos os {{tokens}} visíveis para o clipboard")
        self._btn_copy_all.clicked.connect(self._copy_all)
        h.addWidget(self._btn_copy_all)

        btn_x = QPushButton("✕")
        btn_x.setObjectName("dyn_close")
        btn_x.setFixedSize(20, 20)
        btn_x.setCursor(QCursor(Qt.PointingHandCursor))
        btn_x.clicked.connect(self.hide)
        h.addWidget(btn_x)
        root.addWidget(hdr)

        # Busca
        sw = QWidget()
        sw.setObjectName("dyn_search_wrap")
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(8, 5, 8, 5)
        self._search = QLineEdit()
        self._search.setObjectName("dyn_search")
        self._search.setPlaceholderText("🔍  Filtrar variáveis...")
        self._search.textChanged.connect(self._filter)
        sl.addWidget(self._search)
        root.addWidget(sw)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("dyn_scroll")

        self._content = QWidget()
        self._content.setObjectName("dyn_content")
        self._cl = QVBoxLayout(self._content)
        self._cl.setContentsMargins(0, 4, 0, 8)
        self._cl.setSpacing(0)
        self._cl.addStretch(1)

        scroll.setWidget(self._content)
        root.addWidget(scroll, 1)

    # ── dados ────────────────────────────────────────────────────────────

    def populate(self, context_vars: dict, nodes_data: list[dict]):
        """
        context_vars : {"var": valor, ...}
        nodes_data   : [{"label": "🔷 N2 — ExtractText", "vars": {...}}, ...]
        """
        # limpa linhas anteriores (preserva stretch final)
        while self._cl.count() > 1:
            item = self._cl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_rows = []
        idx = 0

        # nós com dados de execução anteriores
        for nd in nodes_data:
            grp = self._make_group(nd["label"], nd["label"])
            self._cl.insertWidget(idx, grp); idx += 1
            for var, val in nd["vars"].items():
                row = self._make_row(var, val, nd["label"])
                self._cl.insertWidget(idx, row); idx += 1
                self._all_rows.append((row, var, nd["label"]))

        # variáveis do contexto
        if context_vars:
            grp = self._make_group("🔵  Variáveis do Fluxo", "ctx")
            self._cl.insertWidget(idx, grp); idx += 1
            for var, val in context_vars.items():
                row = self._make_row(var, val, "ctx")
                self._cl.insertWidget(idx, row); idx += 1
                self._all_rows.append((row, var, "ctx"))

        if not context_vars and not nodes_data:
            empty = QLabel(
                "  Nenhuma variável disponível ainda.\n"
                "  Execute o fluxo para ver as saídas aqui."
            )
            empty.setObjectName("dyn_empty")
            empty.setWordWrap(True)
            self._cl.insertWidget(0, empty)

        self._filter(self._search.text())

    def _make_group(self, title: str, group_key: str) -> QWidget:
        w = QWidget()
        w.setObjectName("dyn_group_row")
        w.setFixedHeight(26)
        hl = QHBoxLayout(w)
        hl.setContentsMargins(6, 0, 6, 0)
        hl.setSpacing(4)
        lbl = QLabel(title)
        lbl.setObjectName("dyn_group")
        hl.addWidget(lbl, 1)
        btn = QPushButton("📋")
        btn.setObjectName("dyn_copy_group")
        btn.setFixedSize(22, 18)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setToolTip(f"Copiar todos os tokens de '{title}'")
        btn.clicked.connect(lambda _, gk=group_key: self._copy_group(gk))
        hl.addWidget(btn)
        return w

    def _make_row(self, var_name: str, value, group: str) -> QWidget:
        row = QWidget()
        row.setObjectName("dyn_row")
        row.setCursor(QCursor(Qt.PointingHandCursor))
        row.setFixedHeight(36)

        hl = QHBoxLayout(row)
        hl.setContentsMargins(14, 0, 10, 0)
        hl.setSpacing(8)

        if isinstance(value, bool):
            icon = "☑"
        elif isinstance(value, dict):
            icon = "📦"
        elif isinstance(value, list):
            icon = "📋"
        elif isinstance(value, (int, float)):
            icon = "🔢"
        else:
            icon = "🔤"

        lbl_name = QLabel(f"{icon}  {var_name}")
        lbl_name.setObjectName("dyn_var_name")

        val_str = str(value)
        if len(val_str) > 28:
            val_str = val_str[:25] + "…"
        lbl_val = QLabel(val_str)
        lbl_val.setObjectName("dyn_var_val")

        hl.addWidget(lbl_name, 2)
        hl.addWidget(lbl_val, 3)

        token = f"{{{{{var_name}}}}}"
        row.mousePressEvent = lambda _e, t=token: self._row_clicked(t)
        return row

    def _row_clicked(self, token: str):
        self._hide_timer.stop()
        self.variable_selected.emit(token)

    def _copy_all(self):
        """Copia todos os {{tokens}} visíveis para o clipboard."""
        tokens = [f"{{{{{var}}}}}" for row, var, _ in self._all_rows if row.isVisible()]
        if not tokens:
            return
        text = " ".join(tokens)
        QApplication.clipboard().setText(text)
        self._flash_copy_btn(self._btn_copy_all, f"✔ {len(tokens)} tokens copiados")

    def _copy_group(self, group_key: str):
        """Copia os {{tokens}} de um grupo específico."""
        tokens = [f"{{{{{var}}}}}" for row, var, grp in self._all_rows
                  if grp == group_key and row.isVisible()]
        if not tokens:
            return
        text = " ".join(tokens)
        QApplication.clipboard().setText(text)

    def _flash_copy_btn(self, btn: QPushButton, msg: str):
        orig = btn.text()
        btn.setText(msg)
        QTimer.singleShot(1800, lambda: btn.setText(orig))

    def _filter(self, text: str):
        text = text.strip().lower()
        for row, var, group in self._all_rows:
            visible = not text or text in var.lower() or text in group.lower()
            row.setVisible(visible)

    # ── show / hide ──────────────────────────────────────────────────────

    def show_for(self, field, context_vars: dict, nodes_data: list[dict]):
        """Exibe o painel posicionado abaixo do campo `field`."""
        self._target_field = field
        self.populate(context_vars, nodes_data)
        self._search.clear()
        self._reposition(field)
        self._hide_timer.stop()
        self.show()
        self.raise_()

    def _reposition(self, field):
        try:
            gp = field.mapToGlobal(field.rect().bottomLeft())
            # desloca ligeiramente para não sobrepor o campo
            gp.setY(gp.y() + 2)
            self.move(gp)
        except Exception:
            pass

    def schedule_hide(self):
        self._hide_timer.start()

    def cancel_hide(self):
        self._hide_timer.stop()

    def enterEvent(self, event):
        self._hide_timer.stop()
        super().enterEvent(event)

    # ── estilos ──────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            #dyn_panel {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 8px;
            }
            #dyn_header {
                background-color: #181825;
                border-bottom: 1px solid #313244;
                border-radius: 8px 8px 0 0;
            }
            #dyn_title { color: #89b4fa; font-weight: 700; font-size: 12px; }
            #dyn_close {
                background: transparent; border: none;
                color: #585b70; font-size: 11px; border-radius: 4px;
            }
            #dyn_close:hover { color: #f38ba8; background: #313244; }
            #dyn_copy_all {
                background: transparent; border: 1px solid #45475a;
                color: #a6adc8; font-size: 11px; border-radius: 4px;
                padding: 2px 7px;
            }
            #dyn_copy_all:hover { background: #313244; color: #cdd6f4; border-color: #89b4fa; }
            #dyn_copy_group {
                background: transparent; border: none;
                color: #45475a; font-size: 11px; border-radius: 3px;
            }
            #dyn_copy_group:hover { background: #313244; color: #cdd6f4; }
            #dyn_group_row { background-color: #1e1e2e; border-top: 1px solid #313244; }

            #dyn_search_wrap {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
            #dyn_search {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 5px; padding: 4px 8px;
                color: #cdd6f4; font-size: 12px;
            }
            #dyn_search:focus { border-color: #89b4fa; }

            #dyn_scroll, #dyn_content { background-color: #1e1e2e; border: none; }

            #dyn_group {
                color: #585b70; font-size: 10px; font-weight: 800;
                letter-spacing: 0.8px; padding-left: 4px;
                background-color: #1e1e2e;
                border-top: 1px solid #313244;
            }
            #dyn_row { background-color: #1e1e2e; border-bottom: 1px solid #181825; }
            #dyn_row:hover { background-color: #2a2a3e; }

            #dyn_var_name { color: #cdd6f4; font-size: 12px; font-weight: 600; }
            #dyn_var_val  { color: #585b70; font-size: 11px; font-family: monospace; }
            #dyn_empty    { color: #45475a; font-size: 11px; padding: 14px; line-height: 1.6; }

            QScrollBar:vertical { background: #1e1e2e; width: 5px; border-radius: 2px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
