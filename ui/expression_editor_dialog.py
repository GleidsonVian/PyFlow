from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QSplitter, QTreeWidget, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt
import engine.execution_context as ctx
from ui.node_details_dialog import VariableHighlighter, DraggableTreeWidget

class ExpressionEditorDialog(QDialog):
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Expressões Avançado [fx]")
        self.setMinimumSize(800, 500)
        self.result_text = initial_text
        self._build_ui()
        self._apply_styles()
        self._populate_input()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter principal
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo: Variáveis
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_input = QLabel("📥 Variáveis Disponíveis")
        lbl_input.setStyleSheet("font-weight: bold; color: #89b4fa; font-size: 14px;")
        left_layout.addWidget(lbl_input)
        
        lbl_helper = QLabel("💡 Clique duas vezes na variável ou arraste")
        lbl_helper.setStyleSheet("color: #a6adc8; font-size: 11px;")
        left_layout.addWidget(lbl_helper)
        
        self.tree_input = DraggableTreeWidget()
        self.tree_input.setHeaderLabels(["Chave", "Valor"])
        self.tree_input.setColumnWidth(0, 150)
        self.tree_input.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        left_layout.addWidget(self.tree_input)
        
        self.splitter.addWidget(self.left_panel)
        
        # Painel direito: Editor
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_editor = QLabel("📝 Editor")
        lbl_editor.setStyleSheet("font-weight: bold; color: #a6e3a1; font-size: 14px;")
        right_layout.addWidget(lbl_editor)
        
        self.editor = QTextEdit()
        self.editor.setAcceptDrops(True)
        self.editor.setPlainText(self.result_text)
        self.highlighter = VariableHighlighter(self.editor.document())
        right_layout.addWidget(self.editor)
        
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([250, 550])
        
        layout.addWidget(self.splitter)
        
        # Botões inferiores
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("✔️ Salvar Expressão")
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self._save_and_close)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _populate_input(self):
        self.tree_input.clear()
        context_vars = ctx.get()
        if not context_vars:
            from PySide6.QtWidgets import QTreeWidgetItem
            item = QTreeWidgetItem(["(Contexto vazio)", ""])
            self.tree_input.addTopLevelItem(item)
            return

        for k, v in context_vars.items():
            self._add_tree_item(self.tree_input, k, v, k)

    def _add_tree_item(self, parent, key, value, var_path):
        from PySide6.QtWidgets import QTreeWidgetItem
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
        elif isinstance(value, list):
            icon = "📂"
            val_str = f"[ Lista com {len(value)} itens ]"
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            for i, v in enumerate(value[:10]):  
                self._add_tree_item(item, f"[{i}]", v, f"{var_path}[{i}]")
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
        else:
            if isinstance(value, bool): icon = "☑️"
            elif isinstance(value, (int, float)): icon = "🔢"
            val_str = str(value)
            if len(val_str) > 50: val_str = val_str[:50] + "..."
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            if isinstance(parent, QTreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def _on_tree_item_double_clicked(self, item, column):
        var_name = item.data(0, Qt.UserRole)
        if not var_name: return
        text_to_insert = f"{{{{{var_name}}}}}"
        cursor = self.editor.textCursor()
        cursor.insertText(text_to_insert)
        self.editor.setFocus()

    def _save_and_close(self):
        self.result_text = self.editor.toPlainText()
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            #btn_save { background-color: #a6e3a1; color: #11111b; font-weight: 700; padding: 6px 16px; border-radius: 6px; }
            QPushButton { background-color: #313244; color: #cdd6f4; font-weight: 600; padding: 6px 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #45475a; }
            QSplitter::handle { background-color: #313244; }
            QTreeWidget { background-color: #181825; border: 1px solid #313244; border-radius: 6px; color: #cdd6f4; }
            QTreeWidget::item { padding: 4px; }
            QTextEdit { background-color: #1e1e2e; border: 1px solid #89b4fa; border-radius: 6px; color: #cdd6f4; font-family: monospace; font-size: 14px; padding: 10px; }
        """)
