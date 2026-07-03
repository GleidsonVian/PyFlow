import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QSplitter, QTreeWidget, QTreeWidgetItem, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QCheckBox, QComboBox,
    QApplication, QMenu
)
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QIcon, QPixmap, QPainter, QColor, QFontMetrics, QSyntaxHighlighter, QTextCharFormat, QFont
import re
import engine.execution_context as ctx
from ui.dynamic_content_panel import DynamicContentPanel

class VariableHighlighter(QSyntaxHighlighter):
    """Destaca variáveis do tipo {{var_name}} em roxo com fundo suave para visual n8n."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.format = QTextCharFormat()
        self.format.setForeground(QColor("#cba6f7")) # Mauve (Roxo)
        self.format.setFontWeight(QFont.Bold)
        self.format.setBackground(QColor("#45475a")) # Fundo sutil

    def highlightBlock(self, text):
        pattern = r"\{\{[^}]*\}\}"
        for match in re.finditer(pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.format)

class DraggableTreeWidget(QTreeWidget):
    """
    Árvore que permite arrastar itens. O texto gerado no arraste é a sintaxe {{var_name}}.
    Ao arrastar, exibe um balão/pílula roxa flutuando sob o cursor.
    """
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        item = self.currentItem()
        if not item:
            return

        # Recupera o nome da variável guardado no Qt.UserRole
        var_name = item.data(0, Qt.UserRole)
        if not var_name:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{{{{{var_name}}}}}")
        drag.setMimeData(mime_data)

        # 🎨 Renderiza uma pílula premium para o arraste (Catppuccin Mauve)
        pixmap = QPixmap(200, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Pílula Mauve
        painter.setBrush(QColor("#cba6f7"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 190, 26, 6, 6)
        
        # Texto escuro contrastante
        painter.setPen(QColor("#11111b"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        display_text = f"{{{{{var_name}}}}}"
        metrics = QFontMetrics(font)
        elided = metrics.elidedText(display_text, Qt.ElideRight, 170)
        painter.drawText(10, 18, elided)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(10, 13))
        drag.exec(Qt.CopyAction)


class MappableLineEdit(QTextEdit):
    """
    Simula um QLineEdit com suporte a highlighting e Drops de variáveis.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.dialog = None
        self._standard_style = "background-color: #313244; border: 1px solid #45475a; border-radius: 4px; color: #cdd6f4; padding: 4px;"
        self._drag_hover_style = "background-color: #313244; border: 2px dashed #cba6f7; border-radius: 4px; color: #cdd6f4; padding: 3px;"
        self._active_style = "background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 4px; color: #cdd6f4; padding: 3px;"
        self.setStyleSheet(self._standard_style)

        self.setFixedHeight(32)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setTabChangesFocus(True)
        
        self.highlighter = VariableHighlighter(self.document())

    def text(self):
        return self.toPlainText().replace('\n', '')

    def setText(self, text):
        self.setPlainText(text)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            self.setStyleSheet(self._drag_hover_style)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        if self.dialog and self.dialog.last_active_field == self:
            self.setStyleSheet(self._active_style)
        else:
            self.setStyleSheet(self._standard_style)
        event.accept()

    def dropEvent(self, event):
        text_to_drop = event.mimeData().text()
        
        if hasattr(event, "position"):
            pos = event.position().toPoint()
        else:
            pos = event.pos()
            
        cursor = self.cursorForPosition(pos)
        cursor.insertText(text_to_drop)
        self.setFocus()
        event.acceptProposedAction()
        if self.dialog:
            self.dialog.set_active_field(self)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.dialog:
            self.dialog.set_active_field(self)
            self.dialog._show_dynamic_panel(self)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.dialog and hasattr(self.dialog, "_dyn_panel"):
            self.dialog._dyn_panel.schedule_hide()


class MappableTextEdit(QTextEdit):
    """
    QTextEdit customizado que aceita Drops de variáveis.
    Exibe uma borda brilhante e insere o texto na posição exata do cursor.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.dialog = None
        self._standard_style = "background-color: #313244; border: 1px solid #45475a; border-radius: 4px; color: #cdd6f4; padding: 6px;"
        self._drag_hover_style = "background-color: #313244; border: 2px dashed #cba6f7; border-radius: 4px; color: #cdd6f4; padding: 5px;"
        self._active_style = "background-color: #1e1e2e; border: 2px solid #89b4fa; border-radius: 4px; color: #cdd6f4; padding: 5px;"
        self.setStyleSheet(self._standard_style)
        self.highlighter = VariableHighlighter(self.document())

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            self.setStyleSheet(self._drag_hover_style)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        if self.dialog and self.dialog.last_active_field == self:
            self.setStyleSheet(self._active_style)
        else:
            self.setStyleSheet(self._standard_style)
        event.accept()

    def dropEvent(self, event):
        text_to_drop = event.mimeData().text()
        
        if hasattr(event, "position"):
            pos = event.position().toPoint()
        else:
            pos = event.pos()
            
        cursor = self.cursorForPosition(pos)
        cursor.insertText(text_to_drop)
        self.setFocus()
        event.acceptProposedAction()
        if self.dialog:
            self.dialog.set_active_field(self)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.dialog:
            self.dialog.set_active_field(self)
            self.dialog._show_dynamic_panel(self)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.dialog and hasattr(self.dialog, "_dyn_panel"):
            self.dialog._dyn_panel.schedule_hide()


class NodeDetailsDialog(QDialog):
    def __init__(self, canvas_widget, parent=None):
        super().__init__(parent)
        self.canvas_widget = canvas_widget
        self.block = canvas_widget.block_instance
        self.params = canvas_widget.params
        self._fields = {}
        self.last_active_field = None  # Recebe texto ao dar duplo clique

        self.setWindowTitle(f"Detalhes do Nó: {self.block.name}")
        self.setMinimumSize(1100, 680)
        self.resize(1380, 780)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self._build_ui()
        self._apply_styles()
        self._populate_input()
        self._populate_props()
        self._populate_output()

        # Painel de conteúdo dinâmico (Power Automate style)
        self._dyn_panel = DynamicContentPanel(self)
        self._dyn_panel.variable_selected.connect(self._insert_dynamic_token)

        self._update_nav()

    def set_active_field(self, field):
        """Define qual campo está ativo para receber variáveis via clique duplo e o destaca."""
        if self.last_active_field and self.last_active_field != field:
            if hasattr(self.last_active_field, '_standard_style'):
                self.last_active_field.setStyleSheet(self.last_active_field._standard_style)
                
        self.last_active_field = field
        if hasattr(field, '_active_style'):
            field.setStyleSheet(field._active_style)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()

        self._btn_prev = QPushButton("← Anterior")
        self._btn_prev.setObjectName("btn_nav")
        self._btn_prev.setAutoDefault(False)
        self._btn_prev.setDefault(False)
        self._btn_prev.clicked.connect(self._go_prev)
        header.addWidget(self._btn_prev)

        self._lbl_nav = QLabel("")
        self._lbl_nav.setObjectName("lbl_nav")
        self._lbl_nav.setAlignment(Qt.AlignCenter)
        header.addWidget(self._lbl_nav)

        self._btn_next = QPushButton("Próximo →")
        self._btn_next.setObjectName("btn_nav")
        self._btn_next.setAutoDefault(False)
        self._btn_next.setDefault(False)
        self._btn_next.clicked.connect(self._go_next)
        header.addWidget(self._btn_next)

        header.addStretch()

        self._title_lbl = QLabel(f"📝 {self.block.name}")
        self._title_lbl.setObjectName("dialog_title")
        header.addWidget(self._title_lbl)

        header.addStretch()

        btn_test = QPushButton("▶ Testar Nó")
        btn_test.setObjectName("btn_test")
        btn_test.clicked.connect(self._test_node)
        header.addWidget(btn_test)

        btn_save = QPushButton("✔️ Aplicar e Voltar")
        btn_save.setObjectName("btn_save")
        btn_save.setAutoDefault(False)
        btn_save.setDefault(False)
        btn_save.clicked.connect(self._save_and_close)
        header.addWidget(btn_save)

        main_layout.addLayout(header)

        # Splitter principal (3 colunas)
        self.splitter = QSplitter(Qt.Horizontal)

        # Coluna 1: Input Data
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        hdr_row = QHBoxLayout()
        lbl_input = QLabel("📥 Dados de Entrada (Contexto Atual)")
        lbl_input.setObjectName("column_title")
        hdr_row.addWidget(lbl_input, 1)
        self._btn_copy_ctx = QPushButton("📋 Tokens")
        self._btn_copy_ctx.setObjectName("btn_copy_ctx")
        self._btn_copy_ctx.setToolTip("Copia todos os {{tokens}} para o clipboard")
        self._btn_copy_ctx.clicked.connect(self._copy_all_ctx)
        hdr_row.addWidget(self._btn_copy_ctx)

        self._btn_copy_json = QPushButton("{ } JSON")
        self._btn_copy_json.setObjectName("btn_copy_ctx")
        self._btn_copy_json.setToolTip("Copia todo o contexto como JSON formatado")
        self._btn_copy_json.clicked.connect(self._copy_ctx_as_json)
        hdr_row.addWidget(self._btn_copy_json)
        left_layout.addLayout(hdr_row)

        lbl_helper = QLabel("💡 Duplo clique insere no campo ativo · Clique direito copia o token")
        lbl_helper.setStyleSheet("color: #a6adc8; font-size: 11px; padding-bottom: 5px;")
        left_layout.addWidget(lbl_helper)

        self.tree_input = DraggableTreeWidget()
        self.tree_input.setHeaderLabels(["Chave", "Valor"])
        self.tree_input.setColumnWidth(0, 150)
        self.tree_input.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.tree_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_input.customContextMenuRequested.connect(self._tree_context_menu)
        left_layout.addWidget(self.tree_input)
        self.splitter.addWidget(self.left_panel)

        # Coluna 2: Parâmetros (Centro)
        self.center_panel = QWidget()
        center_layout = QVBoxLayout(self.center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        lbl_params = QLabel("⚙ Parâmetros")
        lbl_params.setObjectName("column_title")
        center_layout.addWidget(lbl_params)

        self.props_scroll = QScrollArea()
        self.props_scroll.setWidgetResizable(True)
        self.props_scroll.setFrameShape(QFrame.NoFrame)
        self.props_content = QWidget()
        self.props_content_layout = QVBoxLayout(self.props_content)
        self.props_content_layout.setContentsMargins(12, 12, 12, 12)
        self.props_content_layout.setAlignment(Qt.AlignTop)
        self.props_scroll.setWidget(self.props_content)
        center_layout.addWidget(self.props_scroll)
        self.splitter.addWidget(self.center_panel)

        # Coluna 3: Output Data
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        lbl_output = QLabel("📤 Saída (Após Testar)")
        lbl_output.setObjectName("column_title")
        right_layout.addWidget(lbl_output)

        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setObjectName("txt_output")
        right_layout.addWidget(self.txt_output)
        self.splitter.addWidget(self.right_panel)

        # Configura proporções do splitter — restaura última posição salva
        import json as _json, os as _os
        _cfg = _os.path.join(_os.path.expanduser("~"), ".pyflow_dialog_splitter.json")
        try:
            with open(_cfg) as _f:
                sizes = _json.load(_f)
        except Exception:
            sizes = [190, 680, 380]
        self.splitter.setSizes(sizes)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.splitterMoved.connect(lambda: self._save_splitter())
        main_layout.addWidget(self.splitter)

    def _populate_input(self):
        self.tree_input.clear()
        context_vars = ctx.get()
        if not context_vars:
            item = QTreeWidgetItem(["(Contexto vazio)", ""])
            self.tree_input.addTopLevelItem(item)
            return

        for k, v in context_vars.items():
            self._add_tree_item(self.tree_input, k, v, k)

    def _add_tree_item(self, parent, key, value, var_path):
        """Adiciona itens à árvore recursivamente com ícones e valores formatados."""
        icon = "🔤"
        val_str = ""
        
        if isinstance(value, dict):
            icon = "📦"
            val_str = "{ ... }"
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            for k, v in value.items():
                self._add_tree_item(item, k, v, f"{var_path}.{k}")
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
            item.setExpanded(True)
        elif isinstance(value, list):
            icon = "📂"
            val_str = f"[ Lista com {len(value)} itens ]"
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            for i, v in enumerate(value[:10]):  # limite visual
                self._add_tree_item(item, f"[{i}]", v, f"{var_path}[{i}]")
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
        else:
            if isinstance(value, bool):
                icon = "☑️"
            elif isinstance(value, (int, float)):
                icon = "🔢"
            
            val_str = str(value)
            if len(val_str) > 50:
                val_str = val_str[:50] + "..."
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def _copy_all_ctx(self):
        """Copia todos os {{tokens}} da árvore de contexto para o clipboard."""
        tokens = []
        def _collect(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                var = child.data(0, Qt.UserRole)
                if var:
                    tokens.append(f"{{{{{var}}}}}")
                _collect(child)
        root = self.tree_input.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            var = item.data(0, Qt.UserRole)
            if var:
                tokens.append(f"{{{{{var}}}}}")
            _collect(item)
        if tokens:
            QApplication.clipboard().setText(" ".join(tokens))
            orig = self._btn_copy_ctx.text()
            self._btn_copy_ctx.setText(f"✔ {len(tokens)} copiados")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1800, lambda: self._btn_copy_ctx.setText(orig))

    def _copy_ctx_as_json(self):
        """Copia o contexto atual como JSON formatado para o clipboard."""
        import json as _json
        data = ctx.get()
        if not data:
            return
        try:
            text = _json.dumps(data, indent=2, ensure_ascii=False, default=str)
        except Exception:
            text = str(data)
        QApplication.clipboard().setText(text)
        orig = self._btn_copy_json.text()
        self._btn_copy_json.setText("✔ Copiado!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1800, lambda: self._btn_copy_json.setText(orig))

    def _tree_context_menu(self, pos):
        item = self.tree_input.itemAt(pos)
        if not item:
            return
        var = item.data(0, Qt.UserRole)
        if not var:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#1e1e2e; border:1px solid #45475a; color:#cdd6f4; }
            QMenu::item:selected { background:#313244; }
        """)
        token = f"{{{{{var}}}}}"
        act_token  = menu.addAction(f"📋  Copiar token  {token}")
        act_value  = menu.addAction(f"📄  Copiar valor")
        act_insert = menu.addAction(f"⌨   Inserir no campo ativo")
        chosen = menu.exec(self.tree_input.viewport().mapToGlobal(pos))
        if chosen == act_token:
            QApplication.clipboard().setText(token)
        elif chosen == act_value:
            import json as _json
            raw = ctx.get().get(var.split(".")[0], "")
            # navega dot-notation se necessário
            if "." in var:
                parts = var.split(".")
                val = ctx.get()
                for p in parts:
                    val = val.get(p, "") if isinstance(val, dict) else ""
                raw = val
            try:
                text = _json.dumps(raw, ensure_ascii=False, default=str) if isinstance(raw, (dict, list)) else str(raw)
            except Exception:
                text = str(raw)
            QApplication.clipboard().setText(text)
        elif chosen == act_insert:
            self._insert_dynamic_token(token)

    def _on_tree_item_double_clicked(self, item, column):
        var_name = item.data(0, Qt.UserRole)
        if not var_name:
            return
        
        text_to_insert = f"{{{{{var_name}}}}}"
        
        if hasattr(self, "last_active_field") and self.last_active_field:
            field = self.last_active_field
            if hasattr(field, "textCursor"):
                cursor = field.textCursor()
                cursor.insertText(text_to_insert)
                field.setFocus()

    def _populate_props(self):
        for schema in self.block.params_schema:
            self.props_content_layout.addWidget(self._build_field(schema, self.params))

        # Nota
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        self.props_content_layout.addWidget(sep)
        nota_schema = {
            "name": "nota",
            "label": "📝 Nota / Comentário",
            "type": "str",
            "default": ""
        }
        self.props_content_layout.addWidget(self._build_field(nota_schema, self.params))

    def _build_field(self, schema: dict, params: dict) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(schema["label"])
        lbl.setObjectName("field_label")
        current = params.get(schema["name"], schema.get("default", ""))

        if schema["type"] == "bool":
            row = QHBoxLayout()
            row.addWidget(lbl)
            check = QCheckBox()
            check.setChecked(bool(current))
            self._fields[schema["name"]] = check
            row.addWidget(check)
            row.addStretch()
            layout.addLayout(row)
        elif schema["type"] == "select":
            layout.addWidget(lbl)
            combo = QComboBox()
            options = schema.get("options", [])
            for opt in options:
                combo.addItem(opt.get("label", opt["value"]), opt["value"])
            current_val = str(current)
            for i, opt in enumerate(options):
                if opt["value"] == current_val:
                    combo.setCurrentIndex(i)
                    break
            self._fields[schema["name"]] = combo
            layout.addWidget(combo)
        elif schema["type"] == "text":
            header = QHBoxLayout()
            header.addWidget(lbl)
            header.addStretch()
            btn_fx = QPushButton("fx")
            btn_fx.setObjectName("btn_fx")
            btn_fx.setToolTip("Abrir Editor de Expressões Avançado")
            header.addWidget(btn_fx)
            layout.addLayout(header)
            
            edit = MappableTextEdit()
            edit.dialog = self
            edit.setMinimumHeight(100)
            edit.setPlainText(str(current))
            self._fields[schema["name"]] = edit
            layout.addWidget(edit)
            
            btn_fx.clicked.connect(lambda _, e=edit: self._open_expression_editor(e))
            
            if self.last_active_field is None:
                self.set_active_field(edit)
        else:
            header = QHBoxLayout()
            header.addWidget(lbl)
            header.addStretch()
            btn_fx = QPushButton("fx")
            btn_fx.setObjectName("btn_fx")
            btn_fx.setToolTip("Abrir Editor de Expressões Avançado")
            header.addWidget(btn_fx)
            layout.addLayout(header)
            
            edit = MappableLineEdit()
            edit.dialog = self
            edit.setText(str(current))
            self._fields[schema["name"]] = edit
            layout.addWidget(edit)
            
            btn_fx.clicked.connect(lambda _, e=edit: self._open_expression_editor(e))
            
            if self.last_active_field is None:
                self.set_active_field(edit)

        return container

    def _open_expression_editor(self, field):
        from ui.expression_editor_dialog import ExpressionEditorDialog
        if hasattr(field, "text"):
            current_text = field.text()
        else:
            current_text = field.toPlainText()
            
        dialog = ExpressionEditorDialog(current_text, self)
        if dialog.exec():
            if hasattr(field, "setText"):
                field.setText(dialog.result_text)
            else:
                field.setPlainText(dialog.result_text)

    def _populate_output(self):
        node = self.canvas_widget
        if node._last_result or node._last_data is not None:
            result = {
                "success":  node._last_ok,
                "message":  node._last_result,
                "duration": f"{node._last_duration:.2f}s",
            }
            if node._last_data:
                result["data"] = node._last_data
            try:
                import json as _json
                text = _json.dumps(result, indent=2, ensure_ascii=False, default=str)
            except Exception:
                text = str(result)
            self.txt_output.setPlainText(text)
        else:
            self.txt_output.setPlainText(
                "O nó ainda não foi executado.\n\n"
                "Clique em 'Testar Nó' para executar com os parâmetros atuais."
            )

    def _test_node(self):
        # Primeiro, pega os valores atuais da UI
        self._apply_to_params()
        
        self.txt_output.setPlainText("Executando bloco...")
        from engine.runner import resolve_params
        
        try:
            resolved = resolve_params(self.params, ctx.get())
            result = self.block.execute(resolved)
            
            # Formata resultado em JSON bonito
            try:
                out_str = json.dumps(result, indent=2, ensure_ascii=False)
            except:
                out_str = str(result)
                
            self.txt_output.setPlainText(out_str)
        except ValueError as e:
            error_json = {
                "success": False,
                "message": str(e)
            }
            self.txt_output.setPlainText(json.dumps(error_json, indent=2, ensure_ascii=False))
        
        # Atualiza input se o bloco injetou algo no contexto
        self._populate_input()

    def _apply_to_params(self):
        for name, field in self._fields.items():
            if isinstance(field, QCheckBox):
                self.params[name] = field.isChecked()
            elif isinstance(field, QComboBox):
                self.params[name] = field.currentData()
            elif isinstance(field, MappableLineEdit):
                self.params[name] = field.text().strip()
            elif isinstance(field, QTextEdit):
                self.params[name] = field.toPlainText()
            elif isinstance(field, QLineEdit):
                self.params[name] = field.text().strip()

    def _save_and_close(self):
        self._apply_to_params()
        self.canvas_widget.update_params_label()
        self.accept()

    def _save_splitter(self):
        import json as _json, os as _os
        _cfg = _os.path.join(_os.path.expanduser("~"), ".pyflow_dialog_splitter.json")
        try:
            with open(_cfg, "w") as _f:
                _json.dump(self.splitter.sizes(), _f)
        except Exception:
            pass

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── navegação entre nós ───────────────────────────────────────────────

    def _ordered_nodes(self) -> list:
        """Retorna todos os NodeItems do canvas ordenados por posição X (esquerda→direita)."""
        try:
            from ui.node_canvas import NodeItem
            scene = self.canvas_widget.scene()
            nodes = [item for item in scene.items() if isinstance(item, NodeItem)]
            nodes.sort(key=lambda n: (n.scenePos().x(), n.scenePos().y()))
            return nodes
        except Exception:
            return [self.canvas_widget]

    def _update_nav(self):
        nodes = self._ordered_nodes()
        try:
            idx = nodes.index(self.canvas_widget)
        except ValueError:
            idx = 0
        total = len(nodes)
        self._lbl_nav.setText(f"{idx + 1} / {total}")
        self._btn_prev.setEnabled(idx > 0)
        self._btn_next.setEnabled(idx < total - 1)

    def _go_prev(self):
        self._navigate(-1)

    def _go_next(self):
        self._navigate(+1)

    def _navigate(self, delta: int):
        nodes = self._ordered_nodes()
        try:
            idx = nodes.index(self.canvas_widget)
        except ValueError:
            return
        new_idx = idx + delta
        if not (0 <= new_idx < len(nodes)):
            return
        # salva params do nó atual
        self._apply_to_params()
        self.canvas_widget.update_params_label()
        # carrega novo nó
        target = nodes[new_idx]
        self.canvas_widget = target
        self.block = target.block_instance
        self.params = target.params
        self._fields = {}
        self.last_active_field = None
        self._title_lbl.setText(f"📝 {self.block.name}")
        self.setWindowTitle(f"Detalhes do Nó: {self.block.name}")
        # limpa e repopula painéis
        self._clear_layout(self.props_content_layout)
        self._populate_props()
        self._populate_input()
        self._populate_output()
        self._update_nav()

    # ── conteúdo dinâmico ─────────────────────────────────────────────────

    def _collect_nodes_data(self) -> list[dict]:
        """Coleta _last_data de todos os nós do canvas (exceto o atual)."""
        result = []
        try:
            from ui.node_canvas import NodeItem
            scene = self.canvas_widget.scene()
            for item in scene.items():
                if isinstance(item, NodeItem) and item is not self.canvas_widget:
                    if item._last_data and isinstance(item._last_data, dict):
                        label = f"🔷  #{item._idx + 1} — {item.block_instance.name}"
                        result.append({"label": label, "vars": dict(item._last_data)})
        except Exception:
            pass
        return result

    def _show_dynamic_panel(self, field):
        """Exibe o painel de conteúdo dinâmico ancorado abaixo do campo."""
        context_vars = ctx.get()
        nodes_data = self._collect_nodes_data()
        self._dyn_panel.cancel_hide()
        self._dyn_panel.show_for(field, context_vars, nodes_data)

    def _insert_dynamic_token(self, token: str):
        """Insere o token selecionado no campo atualmente ativo."""
        field = self.last_active_field
        if field is None:
            return
        if hasattr(field, "textCursor"):
            cursor = field.textCursor()
            cursor.insertText(token)
            field.setFocus()
        elif hasattr(field, "insert"):
            field.insert(token)
            field.setFocus()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            #dialog_title { font-size: 18px; font-weight: 700; color: #cba6f7; }
            #column_title { font-size: 14px; font-weight: 600; color: #89b4fa; padding: 5px; }
            #btn_save { background-color: #a6e3a1; color: #11111b; font-weight: 700; padding: 6px 16px; border-radius: 6px; }
            #btn_test { background-color: #89b4fa; color: #11111b; font-weight: 700; padding: 6px 16px; border-radius: 6px; }
            QSplitter::handle { background-color: #313244; }
            QTreeWidget { background-color: #181825; border: 1px solid #313244; border-radius: 6px; color: #cdd6f4; }
            QTreeWidget::item { padding: 4px; }
            QScrollArea, #props_content { background-color: #181825; }
            #txt_output { background-color: #181825; border: 1px solid #313244; border-radius: 6px; color: #a6e3a1; font-family: monospace; font-size: 13px; padding: 10px; }
            #field_label { color: #a6adc8; font-weight: 600; margin-top: 8px; }
            QLineEdit, QTextEdit, QComboBox { background-color: #313244; border: 1px solid #45475a; border-radius: 4px; color: #cdd6f4; padding: 6px; }
            #separator { color: #313244; margin: 10px 0; }
            #btn_fx { background-color: transparent; color: #89b4fa; font-weight: 800; border: 1px solid #45475a; border-radius: 4px; padding: 2px 10px; margin-top: 5px; }
            #btn_fx:hover { background-color: #313244; border-color: #89b4fa; }
            #btn_copy_ctx { background:#313244; color:#a6adc8; border:1px solid #45475a; border-radius:5px; padding:3px 10px; font-size:11px; }
            #btn_copy_ctx:hover { background:#45475a; color:#cdd6f4; }
            #btn_nav { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 14px; font-size: 12px; }
            #btn_nav:hover { background-color: #45475a; }
            #btn_nav:disabled { color: #45475a; border-color: #313244; background-color: #1e1e2e; }
            #lbl_nav { color: #6c7086; font-size: 12px; min-width: 44px; }
        """)
