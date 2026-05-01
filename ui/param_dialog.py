from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QFrame, QWidget
)
from PySide6.QtCore import Qt


def _get_available_variables() -> list[str]:
    try:
        from blocks.browser.extract_text import ExtractTextBlock
        return list(ExtractTextBlock._context.keys())
    except Exception:
        return []


class ParamDialog(QDialog):
    def __init__(self, block_instance, current_params: dict, parent=None):
        super().__init__(parent)
        self.block_instance = block_instance
        self.current_params = current_params
        self._fields = {}

        self.setWindowTitle(f"Configurar: {block_instance.name}")
        self.setModal(True)
        self.setMinimumWidth(440)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel(self.block_instance.name)
        title.setObjectName("dialog_title")
        desc = QLabel(self.block_instance.description)
        desc.setObjectName("dialog_desc")
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("dialog_sep")
        layout.addWidget(sep)

        # Hint de variáveis disponíveis
        variables = _get_available_variables()
        if variables:
            vars_text = "  ".join(f"{{{{ {v} }}}}" for v in variables)
            hint = QLabel(f"📌 Variáveis disponíveis:  {vars_text}")
            hint.setObjectName("vars_hint")
            hint.setWordWrap(True)
            layout.addWidget(hint)

        # Campos dinâmicos
        for schema in self.block_instance.params_schema:
            layout.addWidget(self._build_field(schema))

        # Botões
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Confirmar")
        btn_ok.setObjectName("btn_ok")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_confirm)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _build_field(self, schema: dict) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label_text = schema["label"]
        if schema.get("required"):
            label_text += " *"

        label = QLabel(label_text)
        label.setObjectName("field_label")

        current_val = self.current_params.get(schema["name"], schema.get("default", ""))

        if schema["type"] == "bool":
            check = QCheckBox()
            check.setChecked(bool(current_val))
            check.setObjectName("field_check")
            self._fields[schema["name"]] = check
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(label)
            row.addWidget(check)
            row.addStretch()
            layout.addLayout(row)
        else:
            layout.addWidget(label)
            edit = QLineEdit()
            edit.setObjectName("field_input")
            edit.setText(str(current_val))
            if schema.get("placeholder"):
                edit.setPlaceholderText(schema["placeholder"])
            self._fields[schema["name"]] = edit
            layout.addWidget(edit)

            # Hint de uso de variável apenas em campos de texto
            variables = _get_available_variables()
            if variables:
                tip = QLabel("Use {{ nome_variavel }} para inserir um valor dinâmico")
                tip.setObjectName("field_tip")
                layout.addWidget(tip)

        return container

    def _on_confirm(self):
        for schema in self.block_instance.params_schema:
            if schema.get("required"):
                field = self._fields.get(schema["name"])
                if isinstance(field, QLineEdit) and not field.text().strip():
                    field.setStyleSheet("border: 1.5px solid #f38ba8;")
                    field.setFocus()
                    return
        self.accept()

    def get_params(self) -> dict:
        result = {}
        for schema in self.block_instance.params_schema:
            field = self._fields.get(schema["name"])
            if isinstance(field, QCheckBox):
                result[schema["name"]] = field.isChecked()
            elif isinstance(field, QLineEdit):
                result[schema["name"]] = field.text().strip()
        return result

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            #dialog_title { font-size: 16px; font-weight: 700; color: #cba6f7; }
            #dialog_desc { font-size: 12px; color: #6c7086; }
            #dialog_sep { color: #313244; }
            #vars_hint {
                background-color: #1e2a1e;
                border: 1px solid #a6e3a1;
                border-radius: 6px;
                padding: 6px 10px;
                color: #a6e3a1;
                font-size: 11px;
                font-family: monospace;
            }
            #field_label { font-size: 12px; font-weight: 600; color: #a6adc8; }
            #field_tip { font-size: 10px; color: #45475a; font-style: italic; }
            #field_input {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 7px 10px;
                color: #cdd6f4;
                font-size: 13px;
            }
            #field_input:focus { border-color: #cba6f7; }
            QCheckBox { color: #cdd6f4; font-size: 13px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid #45475a; background: #313244;
            }
            QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }
            #btn_ok {
                background-color: #cba6f7; color: #1e1e2e;
                border-radius: 6px; padding: 7px 20px;
                font-weight: 600; font-size: 13px; border: none;
            }
            #btn_ok:hover { background-color: #d5b8f8; }
            #btn_cancel {
                background-color: #313244; color: #cdd6f4;
                border-radius: 6px; padding: 7px 20px;
                font-size: 13px; border: none;
            }
            #btn_cancel:hover { background-color: #45475a; }
        """)