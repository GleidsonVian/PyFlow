"""
Barra de controle do modo debug do PyFlow RPA.
Aparece na parte superior do canvas durante debug step-by-step.
Coloque em: ui/debug_toolbar.py
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class DebugToolbar(QWidget):
    """
    Barra de controle exibida durante o modo debug.
    Emite signals para o MainWindow controlar o DebugRunner.
    """
    sig_step    = Signal()   # avançar um bloco
    sig_resume  = Signal()   # continuar sem pausar
    sig_stop    = Signal()   # parar debug

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("debug_toolbar")
        self.setFixedHeight(52)
        self._build_ui()
        self._apply_styles()
        self.hide()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        # Badge debug
        badge = QLabel("🐛  DEBUG")
        badge.setObjectName("debug_badge")

        # Info do bloco atual
        self.lbl_info = QLabel("Pronto para iniciar")
        self.lbl_info.setObjectName("debug_info")

        # Progresso
        self.progress = QProgressBar()
        self.progress.setObjectName("debug_progress")
        self.progress.setFixedWidth(120)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)

        self.lbl_progress = QLabel("0 / 0")
        self.lbl_progress.setObjectName("debug_progress_lbl")

        # Botões
        self.btn_step = QPushButton("⏭  Próximo")
        self.btn_step.setObjectName("btn_debug_step")
        self.btn_step.setToolTip("Executar o bloco atual e pausar no próximo")
        self.btn_step.clicked.connect(self.sig_step)

        self.btn_resume = QPushButton("▶  Continuar")
        self.btn_resume.setObjectName("btn_debug_resume")
        self.btn_resume.setToolTip("Executar todos os blocos restantes sem pausar")
        self.btn_resume.clicked.connect(self.sig_resume)

        self.btn_stop = QPushButton("■  Parar")
        self.btn_stop.setObjectName("btn_debug_stop")
        self.btn_stop.setToolTip("Encerrar o modo debug")
        self.btn_stop.clicked.connect(self.sig_stop)

        layout.addWidget(badge)
        layout.addWidget(self.lbl_info, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.lbl_progress)
        layout.addWidget(self.btn_step)
        layout.addWidget(self.btn_resume)
        layout.addWidget(self.btn_stop)

    def update_state(self, index: int, total: int, block_name: str, waiting: bool):
        """Atualiza o estado visual da barra."""
        self.lbl_info.setText(
            f"{'⏸  Aguardando' if waiting else '▶  Executando'}  →  Passo {index + 1}: {block_name}"
        )
        self.progress.setMaximum(total)
        self.progress.setValue(index)
        self.lbl_progress.setText(f"{index} / {total}")
        self.btn_step.setEnabled(waiting)
        self.btn_resume.setEnabled(waiting)

    def set_finished(self, ok: int, total: int):
        self.lbl_info.setText(f"✅  Debug concluído — {ok}/{total} passos com sucesso")
        self.btn_step.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.progress.setValue(total)
        self.lbl_progress.setText(f"{total} / {total}")

    def _apply_styles(self):
        self.setStyleSheet("""
            #debug_toolbar {
                background-color: #1e2a10;
                border-bottom: 2px solid #a6e3a1;
            }
            #debug_badge {
                font-size: 12px; font-weight: 800;
                color: #a6e3a1; letter-spacing: 1px;
            }
            #debug_info {
                font-size: 12px; color: #cdd6f4; font-weight: 500;
            }
            #debug_progress {
                background-color: #313244;
                border-radius: 3px; border: none;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 3px;
            }
            #debug_progress_lbl {
                font-size: 11px; color: #6c7086; font-family: monospace;
            }
            #btn_debug_step {
                background-color: #cba6f7; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 5px 14px; font-weight: 700; font-size: 12px;
            }
            #btn_debug_step:hover { background-color: #d5b8f8; }
            #btn_debug_step:disabled { background-color: #45475a; color: #6c7086; }
            #btn_debug_resume {
                background-color: #a6e3a1; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 5px 14px; font-weight: 700; font-size: 12px;
            }
            #btn_debug_resume:hover { background-color: #b9f0b3; }
            #btn_debug_resume:disabled { background-color: #45475a; color: #6c7086; }
            #btn_debug_stop {
                background-color: #3a1c1c; color: #f38ba8;
                border: 1px solid #f38ba8; border-radius: 6px;
                padding: 5px 12px; font-size: 12px;
            }
            #btn_debug_stop:hover { background-color: #4a2020; }
        """)
