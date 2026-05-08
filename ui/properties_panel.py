from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QCheckBox, QTabWidget, QComboBox,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
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

        # ── Aba Preview ───────────────────────────────────────────────
        self.tab_preview = QWidget()
        self.tab_preview.setObjectName("tab_content")
        prev_layout = QVBoxLayout(self.tab_preview)
        prev_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setObjectName("props_scroll")
        self.preview_scroll.setFrameShape(QFrame.NoFrame)

        self.preview_content = QWidget()
        self.preview_content.setObjectName("props_content")
        self.preview_content_layout = QVBoxLayout(self.preview_content)
        self.preview_content_layout.setContentsMargins(12, 12, 12, 12)
        self.preview_content_layout.setSpacing(10)
        self.preview_content_layout.setAlignment(Qt.AlignTop)

        self.preview_empty = QLabel("Selecione um bloco\npara ver o preview.")
        self.preview_empty.setObjectName("props_empty")
        self.preview_empty.setAlignment(Qt.AlignCenter)
        self.preview_content_layout.addWidget(self.preview_empty)

        self.preview_scroll.setWidget(self.preview_content)
        prev_layout.addWidget(self.preview_scroll)
        self.tabs.addTab(self.tab_preview, "👁  Preview")

        layout.addWidget(self.tabs)

    def show_block(self, canvas_widget):
        self._current_widget = canvas_widget
        self._fields.clear()
        self._clear_layout(self.props_content_layout)
        self._populate_props(canvas_widget)
        self._clear_layout(self.help_content_layout)
        self._populate_help(canvas_widget)
        self._clear_layout(self.preview_content_layout)
        self._populate_preview(canvas_widget)

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

    def _populate_preview(self, canvas_widget):
        """Aba Preview: valida seletor, mostra último valor extraído e screenshot."""
        block  = canvas_widget.block_instance
        params = canvas_widget.params
        block_type = type(block).__name__

        # ── Seletor ───────────────────────────────────────────────────
        selector = params.get("selector", "").strip()
        if selector:
            sel_title = QLabel("Seletor CSS")
            sel_title.setObjectName("preview_section")
            self.preview_content_layout.addWidget(sel_title)

            sel_box = QLabel(selector)
            sel_box.setObjectName("preview_selector")
            sel_box.setWordWrap(True)
            sel_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.preview_content_layout.addWidget(sel_box)

            # Botão verificar
            self._preview_result = QLabel("")
            self._preview_result.setObjectName("preview_result")
            self._preview_result.setWordWrap(True)

            btn_check = QPushButton("Verificar elemento no navegador")
            btn_check.setObjectName("btn_preview_check")
            btn_check.clicked.connect(lambda: self._check_selector(selector))
            self.preview_content_layout.addWidget(btn_check)
            self.preview_content_layout.addWidget(self._preview_result)
            self.preview_content_layout.addWidget(self._sep())

        # ── Último valor extraído (ExtractTextBlock / ExtractListBlock) ──
        var_name = params.get("variable_name", "")
        if var_name:
            try:
                from engine.execution_context import get as ctx_get
                ctx = ctx_get()
                value = ctx.get(var_name)
                if value is not None:
                    val_title = QLabel(f"Valor atual de  {{{{{var_name}}}}}")
                    val_title.setObjectName("preview_section")
                    self.preview_content_layout.addWidget(val_title)

                    display = str(value)
                    if isinstance(value, list):
                        display = f"Lista com {len(value)} itens:\n" + "\n".join(
                            f"  [{i}] {str(v)[:60]}" for i, v in enumerate(value[:8])
                        )
                        if len(value) > 8:
                            display += f"\n  ... +{len(value)-8} mais"
                    elif len(display) > 200:
                        display = display[:200] + "..."

                    val_box = QLabel(display)
                    val_box.setObjectName("preview_value")
                    val_box.setWordWrap(True)
                    val_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    self.preview_content_layout.addWidget(val_box)
                    self.preview_content_layout.addWidget(self._sep())
            except Exception:
                pass

        # ── Screenshot (ScreenshotBlock) ─────────────────────────────
        if block_type == "ScreenshotBlock":
            filename = params.get("filename", "screenshot.png")
            if filename and __import__("os").path.exists(filename):
                img_title = QLabel("Última screenshot")
                img_title.setObjectName("preview_section")
                self.preview_content_layout.addWidget(img_title)

                img_label = QLabel()
                pix = QPixmap(filename)
                if not pix.isNull():
                    pix = pix.scaledToWidth(250, Qt.SmoothTransformation)
                    img_label.setPixmap(pix)
                    img_label.setObjectName("preview_image")
                    img_label.setAlignment(Qt.AlignCenter)
                    self.preview_content_layout.addWidget(img_label)

        # ── URL atual (NavigateToUrlBlock / GetCurrentUrlBlock) ───────
        if block_type in ("NavigateToUrlBlock", "GetCurrentUrlBlock", "OpenBrowserBlock"):
            try:
                from blocks.browser.open_browser import OpenBrowserBlock as _OB
                driver = _OB.get_driver()
                if driver:
                    url_title = QLabel("URL atual do navegador")
                    url_title.setObjectName("preview_section")
                    self.preview_content_layout.addWidget(url_title)
                    url_val = QLabel(driver.current_url)
                    url_val.setObjectName("preview_value")
                    url_val.setWordWrap(True)
                    url_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    self.preview_content_layout.addWidget(url_val)
            except Exception:
                pass

        self.preview_content_layout.addStretch()

    def _check_selector(self, selector: str):
        """Valida o seletor CSS contra o navegador ativo e exibe o resultado."""
        try:
            from blocks.browser.open_browser import OpenBrowserBlock as _OB
            from selenium.webdriver.common.by import By
            driver = _OB.get_driver()
            if not driver:
                self._preview_result.setObjectName("preview_result_warn")
                self._preview_result.setText("Nenhum navegador aberto.")
                self._preview_result.setStyleSheet("color: #fab387; font-size: 12px; padding: 4px;")
                return
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            count = len(elements)
            if count == 0:
                self._preview_result.setText("❌  Elemento NÃO encontrado na página atual.")
                self._preview_result.setStyleSheet(
                    "color: #f38ba8; font-size: 12px; background: #2a1515; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
            elif count == 1:
                tag = elements[0].tag_name
                text = (elements[0].text or "")[:50]
                self._preview_result.setText(
                    f"✅  1 elemento encontrado\n"
                    f"    Tag: <{tag}>\n"
                    f"    Texto: {text}"
                )
                self._preview_result.setStyleSheet(
                    "color: #a6e3a1; font-size: 12px; background: #152a1a; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
            else:
                self._preview_result.setText(
                    f"⚠️  {count} elementos encontrados\n"
                    f"    O seletor não é único — pode pegar o elemento errado."
                )
                self._preview_result.setStyleSheet(
                    "color: #fab387; font-size: 12px; background: #2a2010; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
        except Exception as e:
            self._preview_result.setText(f"Erro: {str(e)[:80]}")
            self._preview_result.setStyleSheet("color: #f38ba8; font-size: 12px;")

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
        self._clear_layout(self.preview_content_layout)

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

            /* Preview tab */
            #preview_section { font-size: 12px; font-weight: 700; color: #89b4fa; margin-top: 4px; }
            #preview_selector {
                background-color: #1e1e2e; border: 1px solid #45475a; border-left: 3px solid #cba6f7;
                border-radius: 5px; padding: 7px 10px; color: #cba6f7;
                font-size: 11px; font-family: monospace;
            }
            #btn_preview_check {
                background-color: #1a2a40; color: #89b4fa; border: 1px solid #89b4fa;
                border-radius: 6px; padding: 6px 12px; font-size: 12px;
            }
            #btn_preview_check:hover { background-color: #1e3a50; }
            #preview_value {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 5px; padding: 8px 10px; color: #a6e3a1;
                font-size: 11px; font-family: monospace;
            }
            #preview_image { padding: 6px 0; }
        """)