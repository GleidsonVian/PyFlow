"""
Dialog de notificação de nova versão do PyFlow RPA.
"""
from __future__ import annotations

import webbrowser

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame
)
from PySide6.QtCore import Qt


class UpdateDialog(QDialog):
    """Exibido quando uma versão mais nova está disponível no GitHub."""

    def __init__(self, current: str, latest: str, release_url: str,
                 notes: str, parent=None):
        super().__init__(parent)
        self.release_url = release_url
        self.setWindowTitle("Nova versão disponível")
        self.setFixedWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._build_ui(current, latest, notes)
        self._apply_styles()

    def _build_ui(self, current: str, latest: str, notes: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 20)

        # Ícone + título
        title = QLabel("⚡  Nova versão do PyFlow RPA")
        title.setObjectName("upd_title")
        layout.addWidget(title)

        # Versões
        ver_row = QHBoxLayout()
        lbl_cur = QLabel(f"Versão atual:  <b>{current}</b>")
        lbl_cur.setObjectName("upd_ver")
        lbl_new = QLabel(f"Nova versão:  <b style='color:#a6e3a1'>{latest}</b>")
        lbl_new.setObjectName("upd_ver")
        lbl_new.setTextFormat(Qt.RichText)
        ver_row.addWidget(lbl_cur)
        ver_row.addStretch()
        ver_row.addWidget(lbl_new)
        layout.addLayout(ver_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("upd_sep")
        layout.addWidget(sep)

        # Notas de release
        if notes.strip():
            lbl_notes = QLabel("O que há de novo:")
            lbl_notes.setObjectName("upd_section")
            layout.addWidget(lbl_notes)

            txt = QTextEdit()
            txt.setReadOnly(True)
            txt.setObjectName("upd_notes")
            txt.setPlainText(notes[:1200])
            txt.setFixedHeight(140)
            layout.addWidget(txt)

        # Botões
        btn_row = QHBoxLayout()
        btn_later = QPushButton("Mais tarde")
        btn_later.setObjectName("upd_btn_later")
        btn_later.clicked.connect(self.reject)

        btn_update = QPushButton("⬇  Baixar atualização")
        btn_update.setObjectName("upd_btn_update")
        btn_update.setDefault(True)
        btn_update.clicked.connect(self._open_release)

        btn_row.addWidget(btn_later)
        btn_row.addStretch()
        btn_row.addWidget(btn_update)
        layout.addLayout(btn_row)

    def _open_release(self):
        webbrowser.open(self.release_url)
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog          { background-color: #1e1e2e; }
            #upd_title       { font-size: 16px; font-weight: 700; color: #cba6f7; }
            #upd_ver         { font-size: 13px; color: #a6adc8; }
            #upd_sep         { color: #313244; }
            #upd_section     { font-size: 12px; color: #6c7086; font-weight: 600; }
            #upd_notes       {
                background: #181825; border: 1px solid #313244;
                border-radius: 6px; color: #cdd6f4;
                font-family: monospace; font-size: 11px; padding: 6px;
            }
            #upd_btn_later   {
                background: transparent; border: 1px solid #45475a;
                color: #6c7086; border-radius: 6px; padding: 7px 18px;
                font-size: 12px;
            }
            #upd_btn_later:hover  { color: #cdd6f4; border-color: #cdd6f4; }
            #upd_btn_update  {
                background: #a6e3a1; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 7px 18px;
                font-size: 12px; font-weight: 700;
            }
            #upd_btn_update:hover { background: #b6f3b1; }
        """)
