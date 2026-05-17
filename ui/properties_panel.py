from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QCheckBox, QComboBox,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal
import engine.execution_context as ctx


def _get_available_variables() -> list[str]:
    return list(ctx.get().keys())


class PropertiesPanel(QWidget):
    params_about_to_change = Signal()   # emitido antes de aplicar alterações (para undo)

    def __init__(self):
        super().__init__()
        self.setObjectName("props_panel")
        self.setMinimumWidth(260)
        self._current_widget = None
        self._fields = {}
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
        layout.addWidget(self.props_scroll)

    def show_block(self, canvas_widget):
        self._current_widget = canvas_widget
        self._fields.clear()
        self._clear_layout(self.props_content_layout)
        self._populate_props(canvas_widget)

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

        # ── Campo de nota (universal — disponível em qualquer bloco) ──
        sep_nota = QFrame()
        sep_nota.setFrameShape(QFrame.HLine)
        sep_nota.setObjectName("separator")
        self.props_content_layout.addWidget(sep_nota)

        nota_schema = {
            "name": "nota",
            "label": "📝  Nota / Comentário",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Opcional — aparece no canvas abaixo do bloco",
        }
        self.props_content_layout.addWidget(self._build_field(nota_schema, params))

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

        elif schema["type"] == "select":
            layout.addWidget(lbl)
            options = schema.get("options", [])

            combo = QComboBox()
            combo.setObjectName("field_select")
            for opt in options:
                combo.addItem(opt.get("label", opt["value"]), opt["value"])

            # Seleciona a opção atual
            current_val = str(current)
            for i, opt in enumerate(options):
                if opt["value"] == current_val:
                    combo.setCurrentIndex(i)
                    break

            # Label de descrição dinâmica
            desc_lbl = QLabel("")
            desc_lbl.setObjectName("field_select_desc")
            desc_lbl.setWordWrap(True)

            def _update_desc(idx, opts=options, lbl=desc_lbl):
                if 0 <= idx < len(opts):
                    lbl.setText(opts[idx].get("description", ""))

            combo.currentIndexChanged.connect(_update_desc)
            _update_desc(combo.currentIndex())

            self._fields[schema["name"]] = combo
            layout.addWidget(combo)
            layout.addWidget(desc_lbl)

        else:
            layout.addWidget(lbl)
            field_name = schema["name"]

            # Detecta campos de seletor CSS → adiciona botão 📍
            is_selector = any(kw in field_name.lower()
                              for kw in ("selector", "seletor"))

            if is_selector:
                row = QHBoxLayout()
                row.setSpacing(4)
                edit = QLineEdit()
                edit.setObjectName("field_input")
                edit.setText(str(current))
                if schema.get("placeholder"):
                    edit.setPlaceholderText(schema["placeholder"])
                self._fields[field_name] = edit
                row.addWidget(edit, 1)

                btn_pick = QPushButton("📍")
                btn_pick.setObjectName("btn_pick_selector")
                btn_pick.setFixedSize(28, 28)
                btn_pick.setToolTip("Capturar seletor clicando no elemento no Chrome")
                # Captura referência ao edit no closure
                def _open_picker(_, e=edit):
                    from ui.selector_picker import SelectorPickerDialog
                    dlg = SelectorPickerDialog(self)
                    if dlg.exec() and dlg.selected_selector:
                        e.setText(dlg.selected_selector)
                btn_pick.clicked.connect(_open_picker)
                row.addWidget(btn_pick)
                layout.addLayout(row)
            else:
                field_name = schema["name"]
                if schema["type"] == "text":
                    edit = QTextEdit()
                    edit.setObjectName("field_text")
                    edit.setMinimumHeight(120)
                    edit.setAcceptRichText(False)
                    edit.setPlaceholderText(schema.get("placeholder", ""))
                    edit.setPlainText(str(current))
                    edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
                    self._fields[field_name] = edit
                    layout.addWidget(edit)
                else:
                    edit = QLineEdit()
                    edit.setObjectName("field_input")
                    edit.setText(str(current))
                    if schema.get("placeholder"):
                        edit.setPlaceholderText(schema["placeholder"])
                    self._fields[field_name] = edit
                    layout.addWidget(edit)

        return container

    def _apply_changes(self):
        if not self._current_widget:
            return
        self.params_about_to_change.emit()   # avisa o canvas para salvar histórico
        for name, field in self._fields.items():
            if isinstance(field, QCheckBox):
                self._current_widget.params[name] = field.isChecked()
            elif isinstance(field, QComboBox):
                self._current_widget.params[name] = field.currentData()
            elif isinstance(field, QTextEdit):
                self._current_widget.params[name] = field.toPlainText()
            elif isinstance(field, QLineEdit):
                self._current_widget.params[name] = field.text().strip()
        self._current_widget.update_params_label()

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        return sep

    def clear(self):
        self._current_widget = None
        self._fields.clear()
        self._clear_layout(self.props_content_layout)

        e1 = QLabel("Selecione um bloco\nno canvas para\neditar suas propriedades.")
        e1.setObjectName("props_empty")
        e1.setAlignment(Qt.AlignCenter)
        self.props_content_layout.addWidget(e1)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _apply_styles(self):
        self.setStyleSheet("""
            #props_panel { background-color: #181825; }
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
            #field_text {
                background-color: #1e1e2e; border: 1px solid #45475a;
                border-radius: 6px; padding: 8px; color: #cdd6f4; font-size: 11px;
            }
            #field_text:focus { border-color: #cba6f7; }
            #field_select {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 4px 8px; color: #cdd6f4; font-size: 12px;
            }
            #field_select:focus { border-color: #cba6f7; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-top: 5px solid #6c7086;
                margin-right: 6px; }
            QComboBox QAbstractItemView {
                background-color: #313244; border: 1px solid #45475a;
                color: #cdd6f4; font-size: 12px; selection-background-color: #45475a;
                outline: none;
            }
            #field_select_desc {
                color: #585b70; font-size: 11px; font-style: italic;
                padding: 2px 4px; min-height: 14px;
            }
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
            #btn_pick_selector {
                background-color: #1e2a3e; color: #89b4fa;
                border: 1px solid #313244; border-radius: 5px;
                font-size: 14px;
            }
            #btn_pick_selector:hover {
                background-color: #263550; border-color: #89b4fa;
            }
        """)