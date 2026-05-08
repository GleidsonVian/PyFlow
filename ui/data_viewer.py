import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

class DataViewerDialog(QDialog):
    def __init__(self, data, block_name="Resultado do Bloco", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"PyFlow Debug: {block_name}")
        self.resize(600, 450)
        
        # Tema Dark Premium
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cba6f7;
                font-size: 14px;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton#btnClose {
                background-color: #f38ba8;
                color: #11111b;
                font-weight: bold;
            }
            QPushButton#btnClose:hover {
                background-color: #fab387;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel(f"📦 Dados de Saída: {block_name}")
        layout.addWidget(header)

        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        
        # Formata JSON se possível
        try:
            if isinstance(data, (dict, list)):
                formatted = json.dumps(data, indent=4, ensure_ascii=False)
            elif isinstance(data, str):
                # Tenta parsear se for string JSON
                try:
                    obj = json.loads(data)
                    formatted = json.dumps(obj, indent=4, ensure_ascii=False)
                except:
                    formatted = data
            else:
                formatted = str(data)
        except Exception as e:
            formatted = f"Erro ao formatar dados: {str(e)}\n\nRaw: {str(data)}"

        self.editor.setPlainText(formatted)
        layout.addWidget(self.editor)

        footer = QHBoxLayout()
        btn_copy = QPushButton("📋 Copiar JSON")
        btn_copy.clicked.connect(self._on_copy)
        
        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.accept)
        
        footer.addWidget(btn_copy)
        footer.addStretch()
        footer.addWidget(btn_close)
        layout.addLayout(footer)

    def _on_copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.editor.toPlainText())
        # Feedback visual simples no botão?
        source = self.sender()
        old_text = source.text()
        source.setText("✅ Copiado!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: source.setText(old_text))
