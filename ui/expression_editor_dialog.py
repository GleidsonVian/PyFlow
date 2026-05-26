import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QSplitter, QTreeWidget, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QTreeWidgetItem,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QKeyEvent, QTextCursor
import engine.execution_context as ctx
from ui.node_details_dialog import VariableHighlighter, DraggableTreeWidget

# ─────────────────────────────────────────────────────────────────────────────
# Funções/snippets disponíveis no autocomplete
# ─────────────────────────────────────────────────────────────────────────────

_BUILTIN_SNIPPETS = [
    # (label exibido,           texto inserido no editor,             categoria)
    # — tudo dentro de {{}} para ser avaliado pelo resolve_params —
    ("len(variavel)",           "{{len(variavel)}}",                  "Função"),
    ("str(variavel)",           "{{str(variavel)}}",                  "Função"),
    ("int(variavel)",           "{{int(variavel)}}",                  "Função"),
    ("float(variavel)",         "{{float(variavel)}}",                "Função"),
    ("round(variavel, 2)",      "{{round(variavel, 2)}}",             "Número"),
    ("abs(variavel)",           "{{abs(variavel)}}",                  "Número"),
    ("min(a, b)",               "{{min(variavel, 0)}}",               "Número"),
    ("max(a, b)",               "{{max(variavel, 0)}}",               "Número"),
    ("variavel.upper()",        "{{variavel.upper()}}",               "Texto"),
    ("variavel.lower()",        "{{variavel.lower()}}",               "Texto"),
    ("variavel.strip()",        "{{variavel.strip()}}",               "Texto"),
    ("variavel.replace(a, b)",  "{{variavel.replace('de', 'para')}}", "Texto"),
    ("variavel.split(sep)",     "{{variavel.split(',')}}",            "Texto"),
    ("len(variavel.split())",   "{{len(variavel.split())}}",          "Texto"),
    ("variavel[0]",             "{{variavel[0]}}",                    "Acesso"),
    ("variavel[-1]",            "{{variavel[-1]}}",                   "Acesso"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Popup de autocomplete (Ctrl+Space ou {{ )
# ─────────────────────────────────────────────────────────────────────────────

class _AutocompletePopup(QListWidget):
    """Popup flutuante de sugestões para o editor fx."""

    def __init__(self, editor: QTextEdit, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self._editor = editor
        self.setObjectName("ac_popup")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(300)
        self.setMaximumHeight(260)
        self.itemClicked.connect(self._on_chosen)
        self.setStyleSheet("""
            QListWidget#ac_popup {
                background: #1e1e2e;
                border: 1.5px solid #89b4fa;
                border-radius: 8px;
                color: #cdd6f4;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget#ac_popup::item            { padding: 5px 10px; border-radius: 4px; }
            QListWidget#ac_popup::item:hover      { background: #313244; }
            QListWidget#ac_popup::item:selected   { background: #45475a; color: #89b4fa; }
        """)

    def populate(self, filter_text: str = ""):
        self.clear()
        ft = filter_text.lower()

        # ── variáveis do contexto ──────────────────────────────────────────────
        variables = list(ctx.get().keys())
        if variables:
            self._add_separator("── Variáveis ──")
            for v in sorted(variables):
                if ft in v.lower():
                    item = QListWidgetItem(f"  {{{{{v}}}}}")
                    item.setData(Qt.UserRole, ("var", f"{{{{{v}}}}}"))
                    item.setToolTip(f"Insere {{{{ {v} }}}}")
                    self.addItem(item)

        # ── snippets de funções ────────────────────────────────────────────────
        self._add_separator("── Funções / Snippets ──")
        for label, snippet, cat in _BUILTIN_SNIPPETS:
            if ft in label.lower() or ft in cat.lower():
                item = QListWidgetItem(f"  {label}   [{cat}]")
                item.setData(Qt.UserRole, ("snippet", snippet))
                item.setToolTip(snippet)
                self.addItem(item)

        if self.count() <= 2:  # só separadores — sem resultados
            self.clear()
            return
        # seleciona primeiro item real
        for i in range(self.count()):
            it = self.item(i)
            if it and it.data(Qt.UserRole):
                self.setCurrentItem(it)
                break

    def _add_separator(self, text: str):
        item = QListWidgetItem(text)
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(Qt.darkGray)
        font = item.font()
        font.setPointSize(9)
        item.setFont(font)
        self.addItem(item)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.currentItem()
            if item and item.data(Qt.UserRole):
                self._on_chosen(item)
            return
        if e.key() == Qt.Key_Escape:
            self.hide()
            self._editor.setFocus()
            return
        # repassa outras teclas para o editor continuar filtrando
        if e.key() not in (Qt.Key_Up, Qt.Key_Down):
            self._editor.setFocus()
            self._editor.keyPressEvent(e)
            return
        super().keyPressEvent(e)

    def _on_chosen(self, item: QListWidgetItem):
        kind, value = item.data(Qt.UserRole)
        self.hide()
        self._insert_into_editor(value)
        self._editor.setFocus()

    def _insert_into_editor(self, text: str):
        """Insere o texto no editor, substituindo o fragmento {{ aberto (se houver)."""
        cursor = self._editor.textCursor()
        # Verifica se há {{ sem fechar antes do cursor
        doc_text   = self._editor.toPlainText()
        pos        = cursor.position()
        before     = doc_text[:pos]
        last_open  = before.rfind("{{")
        last_close = before.rfind("}}")

        if last_open != -1 and (last_close == -1 or last_close < last_open):
            # Remove o {{ incompleto antes de inserir
            chars_to_remove = pos - last_open
            for _ in range(chars_to_remove):
                cursor.deletePreviousChar()

        cursor.insertText(text)
        self._editor.setTextCursor(cursor)


# ─────────────────────────────────────────────────────────────────────────────
# QTextEdit com Ctrl+Space e auto-popup ao digitar {{
# ─────────────────────────────────────────────────────────────────────────────

class _ExprEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup: _AutocompletePopup | None = None

    def set_popup(self, popup: _AutocompletePopup):
        self._popup = popup

    def keyPressEvent(self, e: QKeyEvent):
        # Ctrl+Space → abre popup com tudo
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Space:
            self._open_popup("")
            e.accept()
            return

        super().keyPressEvent(e)

        # Após digitar, verifica se cursor está dentro de {{
        self._check_auto_popup()

    def _check_auto_popup(self):
        if self._popup is None:
            return
        doc_text   = self.toPlainText()
        pos        = self.textCursor().position()
        before     = doc_text[:pos]
        last_open  = before.rfind("{{")
        last_close = before.rfind("}}")

        if last_open != -1 and (last_close == -1 or last_close < last_open):
            filter_text = before[last_open + 2:]
            self._open_popup(filter_text)
        else:
            if self._popup.isVisible():
                self._popup.hide()

    def _open_popup(self, filter_text: str):
        if self._popup is None:
            return
        self._popup.populate(filter_text)
        if self._popup.count() == 0:
            self._popup.hide()
            return
        # Posiciona próximo ao cursor no texto
        cursor_rect = self.cursorRect()
        global_pos  = self.mapToGlobal(
            QPoint(cursor_rect.left(), cursor_rect.bottom() + 4)
        )
        self._popup.move(global_pos)
        self._popup.show()


# ─────────────────────────────────────────────────────────────────────────────
# Dialog principal
# ─────────────────────────────────────────────────────────────────────────────

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

        # ── painel esquerdo: variáveis ─────────────────────────────────────────
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

        # ── painel direito: editor ─────────────────────────────────────────────
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        lbl_editor = QLabel("📝 Editor")
        lbl_editor.setStyleSheet("font-weight: bold; color: #a6e3a1; font-size: 14px;")
        right_layout.addWidget(lbl_editor)

        # dica de atalho
        lbl_hint = QLabel("⌨️  Ctrl+Space  →  sugestões de variáveis e funções")
        lbl_hint.setStyleSheet("color: #585b70; font-size: 11px; font-style: italic;")
        right_layout.addWidget(lbl_hint)

        self.editor = _ExprEditor()
        self.editor.setAcceptDrops(True)
        self.editor.setPlainText(self.result_text)
        self.highlighter = VariableHighlighter(self.editor.document())
        right_layout.addWidget(self.editor)

        # popup — criado aqui para ser filho do diálogo (não do editor)
        self._popup = _AutocompletePopup(self.editor, self)
        self.editor.set_popup(self._popup)

        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([250, 550])

        layout.addWidget(self.splitter)

        # ── botões ────────────────────────────────────────────────────────────
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
            item = QTreeWidgetItem(["(Contexto vazio)", ""])
            self.tree_input.addTopLevelItem(item)
            return
        for k, v in context_vars.items():
            self._add_tree_item(self.tree_input, k, v, k)

    def _add_tree_item(self, parent, key, value, var_path):
        icon = "🔤"
        val_str = ""

        if isinstance(value, dict):
            icon, val_str = "📦", "{ ... }"
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            for k, v in value.items():
                self._add_tree_item(item, k, v, f"{var_path}.{k}")
        elif isinstance(value, list):
            icon, val_str = "📂", f"[ Lista com {len(value)} itens ]"
            item = QTreeWidgetItem([f"{icon}  {key}", val_str])
            item.setData(0, Qt.UserRole, var_path)
            for i, v in enumerate(value[:10]):
                self._add_tree_item(item, f"[{i}]", v, f"{var_path}[{i}]")
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
        cursor = self.editor.textCursor()
        cursor.insertText(f"{{{{{var_name}}}}}")
        self.editor.setFocus()

    def _save_and_close(self):
        self.result_text = self.editor.toPlainText()
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            #btn_save {
                background-color: #a6e3a1; color: #11111b;
                font-weight: 700; padding: 6px 16px; border-radius: 6px;
            }
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                font-weight: 600; padding: 6px 16px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #45475a; }
            QSplitter::handle { background-color: #313244; }
            QTreeWidget {
                background-color: #181825; border: 1px solid #313244;
                border-radius: 6px; color: #cdd6f4;
            }
            QTreeWidget::item { padding: 4px; }
            QTextEdit {
                background-color: #1e1e2e; border: 1px solid #89b4fa;
                border-radius: 6px; color: #cdd6f4;
                font-family: monospace; font-size: 14px; padding: 10px;
            }
        """)
