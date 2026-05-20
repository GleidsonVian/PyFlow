import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QSplitter, QTreeWidget, QTreeWidgetItem, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QIcon, QPixmap, QPainter, QColor, QFontMetrics, QSyntaxHighlighter, QTextCharFormat, QFont
import re
import engine.execution_context as ctx

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


class NodeDetailsDialog(QDialog):
    def __init__(self, canvas_widget, parent=None):
        super().__init__(parent)
        self.canvas_widget = canvas_widget
        self.block = canvas_widget.block_instance
        self.params = canvas_widget.params
        self._fields = {}
        self.last_active_field = None  # Recebe texto ao dar duplo clique

        self.setWindowTitle(f"Detalhes do Nó: {self.block.name}")
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self._build_ui()
        self._apply_styles()
        self._populate_input()
        self._populate_props()
        self._populate_output()

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
        title = QLabel(f"📝 {self.block.name}")
        title.setObjectName("dialog_title")
        header.addWidget(title)
        header.addStretch()
        
        btn_test = QPushButton("▶ Testar Nó")
        btn_test.setObjectName("btn_test")
        btn_test.clicked.connect(self._test_node)
        header.addWidget(btn_test)

        btn_save = QPushButton("✔️ Aplicar e Voltar")
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self._save_and_close)
        header.addWidget(btn_save)

        main_layout.addLayout(header)

        # Splitter principal (3 colunas)
        self.splitter = QSplitter(Qt.Horizontal)

        # Coluna 1: Input Data
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        lbl_input = QLabel("📥 Dados de Entrada (Contexto Atual)")
        lbl_input.setObjectName("column_title")
        left_layout.addWidget(lbl_input)
        
        lbl_helper = QLabel("💡 Dê foco ao campo desejado e clique duas vezes na variável (ou arraste-a)")
        lbl_helper.setStyleSheet("color: #a6adc8; font-size: 11px; padding-bottom: 5px;")
        left_layout.addWidget(lbl_helper)
        
        self.tree_input = DraggableTreeWidget()
        self.tree_input.setHeaderLabels(["Chave", "Valor"])
        self.tree_input.setColumnWidth(0, 150)
        self.tree_input.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
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

        # Configura proporções do splitter
        self.splitter.setSizes([300, 400, 300])
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
        self.txt_output.setPlainText("O nó ainda não foi testado nesta sessão.\n\nClique em 'Testar Nó' acima para executar com os parâmetros atuais.")

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
        
        # Tenta emitir o signal request_save no canvas para já gravar no JSON se houver um arquivo aberto
        if hasattr(self.canvas_widget.scene(), "views"):
            for view in self.canvas_widget.scene().views():
                if hasattr(view, "_canvas") and hasattr(view._canvas, "request_save"):
                    view._canvas.request_save.emit()
                    break
                    
        self.accept()

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
        """)
