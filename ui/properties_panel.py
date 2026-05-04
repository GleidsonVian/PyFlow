from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt
import engine.execution_context as ctx


def _get_available_variables() -> list[str]:
    return list(ctx.get().keys())


class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("props_panel")
        self.setFixedWidth(280)
        self._current_widget = None
        self._fields = {}
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("props_tabs")

        # ── Aba Propriedades ──────────────────────────────────────────
        self.tab_props = QWidget()
        self.tab_props.setObjectName("tab_content")
        props_layout = QVBoxLayout(self.tab_props)
        props_layout.setContentsMargins(0, 0, 0, 0)

        self.props_scroll = QScrollArea()
        self.props_scroll.setWidgetResizable(True)
        self.props_scroll.setObjectName("props_scroll")
        self.props_scroll.setFrameShape(QFrame.NoFrame)

        self.props_content = QWidget()
        self.props_content.setObjectName("props_content")
        self.props_content_layout = QVBoxLayout(self.props_content)
        self.props_content_layout.setContentsMargins(12, 12, 12, 12)
        self.props_content_layout.setSpacing(12)
        self.props_content_layout.setAlignment(Qt.AlignTop)

        self.props_empty = QLabel("Selecione um bloco\nno canvas para\neditar suas propriedades.")
        self.props_empty.setObjectName("props_empty")
        self.props_empty.setAlignment(Qt.AlignCenter)
        self.props_content_layout.addWidget(self.props_empty)

        self.props_scroll.setWidget(self.props_content)
        props_layout.addWidget(self.props_scroll)
        self.tabs.addTab(self.tab_props, "⚙  Propriedades")

        # ── Aba Ajuda ─────────────────────────────────────────────────
        self.tab_help = QWidget()
        self.tab_help.setObjectName("tab_content")
        help_layout = QVBoxLayout(self.tab_help)
        help_layout.setContentsMargins(0, 0, 0, 0)

        self.help_scroll = QScrollArea()
        self.help_scroll.setWidgetResizable(True)
        self.help_scroll.setObjectName("props_scroll")
        self.help_scroll.setFrameShape(QFrame.NoFrame)

        self.help_content = QWidget()
        self.help_content.setObjectName("props_content")
        self.help_content_layout = QVBoxLayout(self.help_content)
        self.help_content_layout.setContentsMargins(12, 12, 12, 12)
        self.help_content_layout.setSpacing(8)
        self.help_content_layout.setAlignment(Qt.AlignTop)

        self.help_empty = QLabel("Selecione um bloco\nno canvas para ver\nsua documentação.")
        self.help_empty.setObjectName("props_empty")
        self.help_empty.setAlignment(Qt.AlignCenter)
        self.help_content_layout.addWidget(self.help_empty)

        self.help_scroll.setWidget(self.help_content)
        help_layout.addWidget(self.help_scroll)
        self.tabs.addTab(self.tab_help, "❓  Ajuda")

        layout.addWidget(self.tabs)

    def show_block(self, canvas_widget):
        self._current_widget = canvas_widget
        self._fields.clear()
        self._clear_layout(self.props_content_layout)
        self._populate_props(canvas_widget)
        self._clear_layout(self.help_content_layout)
        self._populate_help(canvas_widget)

    def _populate_props(self, canvas_widget):
        block  = canvas_widget.block_instance
        params = canvas_widget.params

        name_label = QLabel(block.name)
        name_label.setObjectName("props_block_name")
        self.props_content_layout.addWidget(name_label)

        if block.description:
            desc = QLabel(block.description)
            desc.setObjectName("props_block_desc")
            desc.setWordWrap(True)
            self.props_content_layout.addWidget(desc)

        variables = _get_available_variables()
        if variables:
            vars_text = "\n".join(f"  {{{{ {v} }}}}" for v in variables)
            vars_label = QLabel(f"Variáveis:\n{vars_text}")
            vars_label.setObjectName("props_vars_hint")
            vars_label.setWordWrap(True)
            self.props_content_layout.addWidget(vars_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        self.props_content_layout.addWidget(sep)

        for schema in block.params_schema:
            self.props_content_layout.addWidget(self._build_field(schema, params))

        btn = QPushButton("Aplicar alterações")
        btn.setObjectName("btn_apply")
        btn.clicked.connect(self._apply_changes)
        self.props_content_layout.addWidget(btn)
        self.props_content_layout.addStretch()

    def _build_field(self, schema: dict, params: dict) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label_text = schema["label"] + (" *" if schema.get("required") else "")
        lbl = QLabel(label_text)
        lbl.setObjectName("field_label")

        current = params.get(schema["name"], schema.get("default", ""))

        if schema["type"] == "bool":
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(lbl)
            check = QCheckBox()
            check.setChecked(bool(current))
            self._fields[schema["name"]] = check
            row.addWidget(check)
            row.addStretch()
            layout.addLayout(row)
        else:
            layout.addWidget(lbl)
            edit = QLineEdit()
            edit.setObjectName("field_input")
            edit.setText(str(current))
            if schema.get("placeholder"):
                edit.setPlaceholderText(schema["placeholder"])
            self._fields[schema["name"]] = edit
            layout.addWidget(edit)

        return container

    def _apply_changes(self):
        if not self._current_widget:
            return
        for name, field in self._fields.items():
            if isinstance(field, QCheckBox):
                self._current_widget.params[name] = field.isChecked()
            elif isinstance(field, QLineEdit):
                self._current_widget.params[name] = field.text().strip()
        self._current_widget.update_params_label()

    def _populate_help(self, canvas_widget):
        try:
            from ui.block_docs import BLOCK_DOCS
        except ImportError:
            lbl = QLabel("Arquivo block_docs.py não encontrado.")
            lbl.setObjectName("props_empty")
            lbl.setAlignment(Qt.AlignCenter)
            self.help_content_layout.addWidget(lbl)
            return

        block_name = type(canvas_widget.block_instance).__name__
        doc = BLOCK_DOCS.get(block_name)

        if not doc:
            lbl = QLabel(f"Documentação não disponível\npara {block_name}.")
            lbl.setObjectName("props_empty")
            lbl.setAlignment(Qt.AlignCenter)
            self.help_content_layout.addWidget(lbl)
            return

        title = QLabel(doc["title"])
        title.setObjectName("help_title")
        self.help_content_layout.addWidget(title)

        desc = QLabel(doc["description"])
        desc.setObjectName("help_desc")
        desc.setWordWrap(True)
        self.help_content_layout.addWidget(desc)

        self.help_content_layout.addWidget(self._sep())

        if doc["params"]:
            lbl_params = QLabel("📋  Parâmetros")
            lbl_params.setObjectName("help_section")
            self.help_content_layout.addWidget(lbl_params)

            for name, tipo, obrig, descricao in doc["params"]:
                self.help_content_layout.addWidget(
                    self._build_param_row(name, tipo, obrig, descricao)
                )

            self.help_content_layout.addWidget(self._sep())

        if doc.get("example"):
            lbl_ex = QLabel("💡  Exemplo")
            lbl_ex.setObjectName("help_section")
            self.help_content_layout.addWidget(lbl_ex)

            ex_box = QLabel(doc["example"])
            ex_box.setObjectName("help_example")
            ex_box.setWordWrap(True)
            self.help_content_layout.addWidget(ex_box)

            self.help_content_layout.addWidget(self._sep())

        if doc.get("tip"):
            tip_box = QLabel("⚡  " + doc["tip"])
            tip_box.setObjectName("help_tip")
            tip_box.setWordWrap(True)
            self.help_content_layout.addWidget(tip_box)

        self.help_content_layout.addStretch()

    def _build_param_row(self, name, tipo, obrig, descricao) -> QWidget:
        w = QWidget()
        w.setObjectName("param_row")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        header = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setObjectName("param_name")
        lbl_tipo = QLabel(tipo)
        lbl_tipo.setObjectName("param_type")
        obrig_text = "obrigatório" if obrig == "Sim" else "opcional" if obrig == "Não" else "condicional"
        obrig_id   = "param_required" if obrig == "Sim" else "param_optional"
        lbl_obrig  = QLabel(obrig_text)
        lbl_obrig.setObjectName(obrig_id)
        header.addWidget(lbl_name)
        header.addWidget(lbl_tipo)
        header.addStretch()
        header.addWidget(lbl_obrig)
        layout.addLayout(header)

        lbl_desc = QLabel(descricao)
        lbl_desc.setObjectName("param_desc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        return w

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        return sep

    def clear(self):
        self._current_widget = None
        self._fields.clear()
        self._clear_layout(self.props_content_layout)
        self._clear_layout(self.help_content_layout)

        e1 = QLabel("Selecione um bloco\nno canvas para\neditar suas propriedades.")
        e1.setObjectName("props_empty")
        e1.setAlignment(Qt.AlignCenter)
        self.props_content_layout.addWidget(e1)

        e2 = QLabel("Selecione um bloco\nno canvas para ver\nsua documentação.")
        e2.setObjectName("props_empty")
        e2.setAlignment(Qt.AlignCenter)
        self.help_content_layout.addWidget(e2)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _apply_styles(self):
        self.setStyleSheet("""
            #props_panel { background-color: #181825; }
            QTabWidget::pane { border: none; background-color: #181825; }
            QTabBar::tab {
                background-color: #1e1e2e; color: #6c7086;
                padding: 8px 14px; font-size: 12px; font-weight: 500;
                border: none; border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #cba6f7; border-bottom: 2px solid #cba6f7; background-color: #181825; }
            QTabBar::tab:hover { color: #cdd6f4; background-color: #313244; }
            #tab_content { background-color: #181825; }
            #props_scroll, #props_content { background-color: #181825; border: none; }
            #props_empty { color: #45475a; font-size: 12px; padding: 30px 10px; }
            #props_block_name { font-size: 14px; font-weight: 700; color: #cba6f7; }
            #props_block_desc { font-size: 11px; color: #6c7086; }
            #props_vars_hint {
                background-color: #1e2a1e; border: 1px solid #a6e3a1;
                border-radius: 6px; padding: 6px 8px;
                color: #a6e3a1; font-size: 11px; font-family: monospace;
            }
            #separator { color: #313244; }
            #field_label { font-size: 12px; font-weight: 600; color: #a6adc8; }
            #field_input {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 6px 10px; color: #cdd6f4; font-size: 12px;
            }
            #field_input:focus { border-color: #cba6f7; }
            QCheckBox { color: #cdd6f4; font-size: 12px; }
            QCheckBox::indicator {
                width: 15px; height: 15px; border-radius: 4px;
                border: 1px solid #45475a; background: #313244;
            }
            QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }
            #btn_apply {
                background-color: #89b4fa; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 7px 12px; font-weight: 600;
                font-size: 12px; margin-top: 4px;
            }
            #btn_apply:hover { background-color: #9ec5fb; }
            #help_title { font-size: 14px; font-weight: 700; color: #cba6f7; }
            #help_desc { font-size: 12px; color: #a6adc8; }
            #help_section { font-size: 12px; font-weight: 700; color: #89b4fa; }
            #help_example {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-left: 3px solid #cba6f7; border-radius: 4px;
                padding: 8px 10px; color: #cdd6f4; font-size: 11px; font-family: monospace;
            }
            #help_tip {
                background-color: #1e2a1e; border: 1px solid #a6e3a1;
                border-radius: 6px; padding: 8px 10px; color: #a6e3a1; font-size: 11px;
            }
            #param_row {
                background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px;
            }
            #param_name { font-size: 12px; font-weight: 700; color: #cdd6f4; font-family: monospace; }
            #param_type { font-size: 11px; color: #fab387; margin-left: 6px; }
            #param_required { font-size: 10px; color: #f38ba8; }
            #param_optional { font-size: 10px; color: #6c7086; }
            #param_desc { font-size: 11px; color: #6c7086; }
        """)