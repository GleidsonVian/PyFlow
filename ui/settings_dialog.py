"""
Painel de configurações de execução do PyFlow RPA.
Coloque em: ui/settings_dialog.py
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙  Configurações de Execução")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()
        self._apply_styles()
        self._load_current()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Título ────────────────────────────────────────────────────
        title = QLabel("⚙  Configurações de Execução")
        title.setObjectName("settings_title")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("settings_sep")
        root.addWidget(sep)

        # ── Grupo Retry ───────────────────────────────────────────────
        group_retry = QGroupBox("Retry automático")
        group_retry.setObjectName("settings_group")
        retry_layout = QVBoxLayout(group_retry)
        retry_layout.setSpacing(12)

        # Ativar retry
        self.chk_retry = QCheckBox("Ativar retry automático quando um bloco falhar")
        self.chk_retry.setObjectName("settings_check")
        self.chk_retry.toggled.connect(self._on_retry_toggled)
        retry_layout.addWidget(self.chk_retry)

        # Número de tentativas
        row_attempts = QHBoxLayout()
        lbl_attempts = QLabel("Número de tentativas extras:")
        lbl_attempts.setObjectName("settings_label")
        self.spin_attempts = QSpinBox()
        self.spin_attempts.setObjectName("settings_spin")
        self.spin_attempts.setRange(1, 10)
        self.spin_attempts.setValue(3)
        self.spin_attempts.setFixedWidth(80)
        self.spin_attempts.setSuffix(" tentativas")
        row_attempts.addWidget(lbl_attempts)
        row_attempts.addStretch()
        row_attempts.addWidget(self.spin_attempts)
        retry_layout.addLayout(row_attempts)

        # Delay entre tentativas
        row_delay = QHBoxLayout()
        lbl_delay = QLabel("Intervalo entre tentativas:")
        lbl_delay.setObjectName("settings_label")
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setObjectName("settings_spin")
        self.spin_delay.setRange(0.5, 60.0)
        self.spin_delay.setValue(2.0)
        self.spin_delay.setSingleStep(0.5)
        self.spin_delay.setFixedWidth(100)
        self.spin_delay.setSuffix(" segundos")
        row_delay.addWidget(lbl_delay)
        row_delay.addStretch()
        row_delay.addWidget(self.spin_delay)
        retry_layout.addLayout(row_delay)

        # Nota explicativa
        nota = QLabel(
            "💡 O retry executa o bloco novamente automaticamente quando ele retorna erro.\n"
            "   Útil para falhas temporárias de rede ou elementos que demoram para carregar."
        )
        nota.setObjectName("settings_nota")
        nota.setWordWrap(True)
        retry_layout.addWidget(nota)

        root.addWidget(group_retry)

        # ── Grupo Comportamento ───────────────────────────────────────
        group_behavior = QGroupBox("Comportamento em caso de falha")
        group_behavior.setObjectName("settings_group")
        beh_layout = QVBoxLayout(group_behavior)
        beh_layout.setSpacing(12)

        self.chk_stop = QCheckBox("Parar execução quando um bloco falhar definitivamente")
        self.chk_stop.setObjectName("settings_check")
        self.chk_stop.setChecked(True)
        beh_layout.addWidget(self.chk_stop)

        nota2 = QLabel(
            "💡 Desmarcado: o fluxo continua mesmo se um bloco falhar,\n"
            "   pulando para o próximo bloco e registrando o erro no log."
        )
        nota2.setObjectName("settings_nota")
        nota2.setWordWrap(True)
        beh_layout.addWidget(nota2)

        root.addWidget(group_behavior)

        root.addStretch()

        # ── Botões ────────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("settings_sep")
        root.addWidget(sep2)

        btn_row = QHBoxLayout()

        btn_reset = QPushButton("Restaurar padrões")
        btn_reset.setObjectName("btn_reset")
        btn_reset.clicked.connect(self._on_reset)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("✓  Salvar")
        btn_save.setObjectName("btn_save")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _load_current(self):
        """Carrega as configurações atuais do runner."""
        from engine.runner import get_runner_config
        cfg = get_runner_config()
        self.chk_retry.setChecked(cfg.retry_enabled)
        self.spin_attempts.setValue(cfg.retry_attempts)
        self.spin_delay.setValue(cfg.retry_delay)
        self.chk_stop.setChecked(cfg.stop_on_failure)
        self._on_retry_toggled(cfg.retry_enabled)

    def _on_retry_toggled(self, enabled: bool):
        self.spin_attempts.setEnabled(enabled)
        self.spin_delay.setEnabled(enabled)

    def _on_reset(self):
        self.chk_retry.setChecked(False)
        self.spin_attempts.setValue(3)
        self.spin_delay.setValue(2.0)
        self.chk_stop.setChecked(True)
        self._on_retry_toggled(False)

    def _on_save(self):
        from engine.runner import get_runner_config
        cfg = get_runner_config()
        cfg.retry_enabled   = self.chk_retry.isChecked()
        cfg.retry_attempts  = self.spin_attempts.value()
        cfg.retry_delay     = self.spin_delay.value()
        cfg.stop_on_failure = self.chk_stop.isChecked()
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }

            #settings_title { font-size: 15px; font-weight: 700; color: #cba6f7; }
            #settings_sep { color: #313244; }

            QGroupBox {
                font-size: 13px; font-weight: 600; color: #89b4fa;
                border: 1px solid #313244; border-radius: 8px;
                margin-top: 8px; padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px; left: 12px;
            }

            #settings_label { font-size: 12px; color: #a6adc8; }
            #settings_nota  { font-size: 11px; color: #45475a; font-style: italic; }

            #settings_check { font-size: 13px; color: #cdd6f4; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid #45475a; background: #313244;
            }
            QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }

            QSpinBox, QDoubleSpinBox {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 8px;
                color: #cdd6f4; font-size: 12px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #cba6f7; }
            QSpinBox:disabled, QDoubleSpinBox:disabled { color: #45475a; }

            #btn_save {
                background-color: #cba6f7; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 7px 20px;
                font-weight: 700; font-size: 13px;
            }
            #btn_save:hover { background-color: #d5b8f8; }

            #btn_cancel {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 7px 16px; font-size: 13px;
            }
            #btn_cancel:hover { background-color: #45475a; }

            #btn_reset {
                background-color: transparent; color: #6c7086; border: none;
                font-size: 12px; text-decoration: underline;
            }
            #btn_reset:hover { color: #cdd6f4; }
        """)
