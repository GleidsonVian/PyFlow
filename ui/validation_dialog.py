from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont


class ValidationDialog(QDialog):
    def __init__(self, issues: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validação do fluxo")
        self.setMinimumSize(560, 380)
        self._proceed = False
        self._build_ui(issues)
        self._apply_styles()

    def _build_ui(self, issues):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        errors   = [x for x in issues if x["level"] == "error"]
        warnings = [x for x in issues if x["level"] == "warning"]

        summary = QLabel(
            f"{'❌' if errors else '⚠️'}  {len(errors)} erro(s)  •  {len(warnings)} aviso(s) encontrado(s)"
        )
        summary.setObjectName("val_summary")
        root.addWidget(summary)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("val_sep")
        root.addWidget(sep)

        self.list = QListWidget()
        self.list.setObjectName("val_list")
        for issue in issues:
            color  = "#f38ba8" if issue["level"] == "error" else "#fab387"
            bg     = "#2e1a1a" if issue["level"] == "error" else "#2e2010"
            icon   = "❌" if issue["level"] == "error" else "⚠"
            text   = f"  {icon}  Passo {issue['step']} — {issue['block']}:  {issue['msg']}"
            item   = QListWidgetItem(text)
            item.setForeground(QColor(color))
            item.setBackground(QColor(bg))
            item.setSizeHint(QSize(0, 26))
            item.setFont(QFont("Consolas", 10))
            self.list.addItem(item)
        root.addWidget(self.list, 1)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("✕  Cancelar e corrigir")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_proceed = QPushButton("▶  Executar mesmo assim")
        btn_proceed.setObjectName("btn_proceed")
        btn_proceed.setEnabled(not errors)
        btn_proceed.clicked.connect(self._on_proceed)

        if errors:
            note = QLabel("Erros impedem a execução")
            note.setObjectName("val_note")
            btn_row.addWidget(note)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_proceed)
        root.addLayout(btn_row)

    def _on_proceed(self):
        self._proceed = True
        self.accept()

    def should_proceed(self) -> bool:
        return self._proceed

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; font-size: 13px; }
            #val_summary { font-size: 14px; font-weight: 600; color: #fab387; padding: 4px 0; }
            #val_sep { color: #313244; }
            #val_note { font-size: 11px; color: #f38ba8; }
            #val_list { background-color: #11111b; border: 1px solid #313244; border-radius: 6px; }
            #val_list::item { padding: 2px 4px; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 18px; font-size: 12px; font-weight: 600; }
            #btn_cancel  { background-color: #313244; color: #cdd6f4; }
            #btn_cancel:hover { background-color: #45475a; }
            #btn_proceed { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_proceed:hover { background-color: #b9f0b3; }
            #btn_proceed:disabled { background-color: #313244; color: #45475a; }
        """)
