"""
ui/settings_dialog.py — Configurações de execução com ConditionalRetry
Integrado ao runner.py existente (preserva AssetManager e lógica atual).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙  Configurações de Execução")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self._apply_styles()
        self._load_current()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("⚙  Configurações de Execução")
        title.setObjectName("settings_title")
        root.addWidget(title)
        root.addWidget(self._sep())

        # ── Retry básico ──────────────────────────────────────────────
        group_retry = QGroupBox("Retry automático")
        group_retry.setObjectName("settings_group")
        retry_layout = QVBoxLayout(group_retry)
        retry_layout.setSpacing(10)

        self.chk_retry = QCheckBox("Ativar retry automático quando um bloco falhar")
        self.chk_retry.setObjectName("settings_check")
        self.chk_retry.toggled.connect(self._on_retry_toggled)
        retry_layout.addWidget(self.chk_retry)

        row_attempts = QHBoxLayout()
        lbl_attempts = QLabel("Número de tentativas extras:")
        lbl_attempts.setObjectName("settings_label")
        self.spin_attempts = QSpinBox()
        self.spin_attempts.setObjectName("settings_spin")
        self.spin_attempts.setRange(1, 10)
        self.spin_attempts.setValue(3)
        self.spin_attempts.setFixedWidth(110)
        self.spin_attempts.setSuffix(" tentativas")
        row_attempts.addWidget(lbl_attempts)
        row_attempts.addStretch()
        row_attempts.addWidget(self.spin_attempts)
        retry_layout.addLayout(row_attempts)

        row_delay = QHBoxLayout()
        lbl_delay = QLabel("Intervalo entre tentativas:")
        lbl_delay.setObjectName("settings_label")
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setObjectName("settings_spin")
        self.spin_delay.setRange(0.5, 60.0)
        self.spin_delay.setValue(2.0)
        self.spin_delay.setSingleStep(0.5)
        self.spin_delay.setFixedWidth(110)
        self.spin_delay.setSuffix(" segundos")
        row_delay.addWidget(lbl_delay)
        row_delay.addStretch()
        row_delay.addWidget(self.spin_delay)
        retry_layout.addLayout(row_delay)

        root.addWidget(group_retry)

        # ── ConditionalRetry ──────────────────────────────────────────
        self.group_cond = QGroupBox("ConditionalRetry — quando fazer retry?")
        self.group_cond.setObjectName("settings_group_cond")
        cond_layout = QVBoxLayout(self.group_cond)
        cond_layout.setSpacing(6)

        desc = QLabel(
            "Defina quais tipos de erro devem acionar o retry.\n"
            "Erros definitivos (seletor inválido, sintaxe errada) nunca se resolvem sozinhos."
        )
        desc.setObjectName("settings_nota")
        desc.setWordWrap(True)
        cond_layout.addWidget(desc)
        cond_layout.addWidget(self._sep())

        self.chk_timeout  = self._make_check(
            "⏱  Timeout / elemento não carregou",
            "TimeoutException — o elemento demorou para aparecer. Retry geralmente resolve.",
            checked=True)
        self.chk_network  = self._make_check(
            "🌐  Erro de rede / conexão",
            "ConnectionError, ERR_CONNECTION — falha temporária de rede. Retry resolve.",
            checked=True)
        self.chk_stale    = self._make_check(
            "♻  Elemento desatualizado (StaleElement)",
            "StaleElementReferenceException — página recarregou. Retry resolve.",
            checked=True)
        self.chk_notfound = self._make_check(
            "🔍  Elemento não encontrado (NoSuchElement)",
            "Seletor CSS não achou o elemento. Retry raramente resolve — revise o seletor.",
            checked=False)
        self.chk_invalid  = self._make_check(
            "❌  Seletor inválido / erro de sintaxe",
            "InvalidSelectorException — seletor com erro de sintaxe. Retry NUNCA resolve.",
            checked=False)

        for w in [self.chk_timeout, self.chk_network, self.chk_stale,
                  self.chk_notfound, self.chk_invalid]:
            cond_layout.addWidget(w)

        cond_layout.addWidget(self._sep())

        lbl_custom = QLabel("🔑  Palavras-chave personalizadas (separadas por vírgula):")
        lbl_custom.setObjectName("settings_label")
        cond_layout.addWidget(lbl_custom)

        self.edit_custom = QLineEdit()
        self.edit_custom.setObjectName("settings_input")
        self.edit_custom.setPlaceholderText("Ex: captcha, rate limit, 503")
        cond_layout.addWidget(self.edit_custom)

        nota_kw = QLabel("Se a mensagem de erro contiver qualquer uma dessas palavras, o retry será acionado.")
        nota_kw.setObjectName("settings_nota")
        nota_kw.setWordWrap(True)
        cond_layout.addWidget(nota_kw)

        root.addWidget(self.group_cond)

        # ── Comportamento ─────────────────────────────────────────────
        group_behavior = QGroupBox("Comportamento em caso de falha")
        group_behavior.setObjectName("settings_group")
        beh_layout = QVBoxLayout(group_behavior)

        self.chk_stop = QCheckBox("Parar execução quando um bloco falhar definitivamente")
        self.chk_stop.setObjectName("settings_check")
        self.chk_stop.setChecked(True)
        beh_layout.addWidget(self.chk_stop)

        nota2 = QLabel(
            "Desmarcado: o fluxo continua mesmo após falha definitiva, pulando para o próximo bloco."
        )
        nota2.setObjectName("settings_nota")
        nota2.setWordWrap(True)
        beh_layout.addWidget(nota2)

        root.addWidget(group_behavior)

        # ── Configurações do Navegador ────────────────────────────────
        group_browser = QGroupBox("🌐  Navegador (Chrome)")
        group_browser.setObjectName("settings_group")
        br_layout = QVBoxLayout(group_browser)
        br_layout.setSpacing(10)

        self.chk_headless = QCheckBox("Modo Headless — Chrome sem janela (produção/servidor)")
        self.chk_headless.setObjectName("settings_check")
        self.chk_headless.toggled.connect(self._on_headless_toggled)
        br_layout.addWidget(self.chk_headless)

        nota_hl = QLabel(
            "Headless: o Chrome roda invisível — mais rápido, sem interferir na tela.\n"
            "Ideal para servidores ou execuções agendadas em background."
        )
        nota_hl.setObjectName("settings_nota")
        nota_hl.setWordWrap(True)
        br_layout.addWidget(nota_hl)

        br_layout.addWidget(self._sep())

        self.chk_disable_images = QCheckBox("Desativar carregamento de imagens (mais rápido)")
        self.chk_disable_images.setObjectName("settings_check")
        br_layout.addWidget(self.chk_disable_images)

        self.chk_incognito = QCheckBox("Modo anônimo (incógnito)")
        self.chk_incognito.setObjectName("settings_check")
        br_layout.addWidget(self.chk_incognito)

        row_size = QHBoxLayout()
        lbl_size = QLabel("Resolução (headless):")
        lbl_size.setObjectName("settings_label")
        self.spin_w = QSpinBox()
        self.spin_w.setObjectName("settings_spin")
        self.spin_w.setRange(800, 3840)
        self.spin_w.setValue(1920)
        self.spin_w.setFixedWidth(90)
        self.spin_w.setSuffix(" px")
        lbl_x = QLabel("×")
        lbl_x.setObjectName("settings_label")
        self.spin_h = QSpinBox()
        self.spin_h.setObjectName("settings_spin")
        self.spin_h.setRange(600, 2160)
        self.spin_h.setValue(1080)
        self.spin_h.setFixedWidth(90)
        self.spin_h.setSuffix(" px")
        row_size.addWidget(lbl_size)
        row_size.addStretch()
        row_size.addWidget(self.spin_w)
        row_size.addWidget(lbl_x)
        row_size.addWidget(self.spin_h)
        br_layout.addLayout(row_size)

        lbl_ua = QLabel("User-Agent personalizado (opcional):")
        lbl_ua.setObjectName("settings_label")
        br_layout.addWidget(lbl_ua)
        self.edit_ua = QLineEdit()
        self.edit_ua.setObjectName("settings_input")
        self.edit_ua.setPlaceholderText("Deixe vazio para usar o padrão do Chrome")
        br_layout.addWidget(self.edit_ua)

        root.addWidget(group_browser)
        root.addStretch()
        root.addWidget(self._sep())

        # ── Botões ────────────────────────────────────────────────────
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

    def _make_check(self, label: str, tooltip: str, checked: bool) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        chk = QCheckBox(label)
        chk.setObjectName("settings_check")
        chk.setChecked(checked)
        tip = QLabel(f"  {tooltip}")
        tip.setObjectName("settings_nota")
        tip.setWordWrap(True)
        layout.addWidget(chk)
        layout.addWidget(tip)
        container._checkbox = chk
        return container

    def _get_chk(self, container) -> QCheckBox:
        return container._checkbox

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("settings_sep")
        return sep

    def _load_current(self):
        from engine.runner import get_runner_config
        from engine.browser_config import get_browser_config
        cfg = get_runner_config()
        self.chk_retry.setChecked(cfg.retry_enabled)
        self.spin_attempts.setValue(cfg.retry_attempts)
        self.spin_delay.setValue(cfg.retry_delay)
        self.chk_stop.setChecked(cfg.stop_on_failure)
        self._get_chk(self.chk_timeout).setChecked(getattr(cfg, "retry_on_timeout",  True))
        self._get_chk(self.chk_network).setChecked(getattr(cfg, "retry_on_network",  True))
        self._get_chk(self.chk_stale).setChecked(getattr(cfg,   "retry_on_stale",    True))
        self._get_chk(self.chk_notfound).setChecked(getattr(cfg,"retry_on_notfound", False))
        self._get_chk(self.chk_invalid).setChecked(getattr(cfg, "retry_on_invalid",  False))
        self.edit_custom.setText(getattr(cfg, "retry_on_custom", ""))
        self._on_retry_toggled(cfg.retry_enabled)
        # Navegador
        bcfg = get_browser_config()
        self.chk_headless.setChecked(bcfg.headless)
        self.chk_disable_images.setChecked(bcfg.disable_images)
        self.chk_incognito.setChecked(bcfg.incognito)
        self.spin_w.setValue(bcfg.window_width)
        self.spin_h.setValue(bcfg.window_height)
        self.edit_ua.setText(bcfg.user_agent)
        self._on_headless_toggled(bcfg.headless)

    def _on_retry_toggled(self, enabled: bool):
        self.spin_attempts.setEnabled(enabled)
        self.spin_delay.setEnabled(enabled)
        self.group_cond.setEnabled(enabled)

    def _on_headless_toggled(self, enabled: bool):
        self.spin_w.setEnabled(enabled)
        self.spin_h.setEnabled(enabled)

    def _on_reset(self):
        self.chk_retry.setChecked(False)
        self.spin_attempts.setValue(3)
        self.spin_delay.setValue(2.0)
        self.chk_stop.setChecked(True)
        self._get_chk(self.chk_timeout).setChecked(True)
        self._get_chk(self.chk_network).setChecked(True)
        self._get_chk(self.chk_stale).setChecked(True)
        self._get_chk(self.chk_notfound).setChecked(False)
        self._get_chk(self.chk_invalid).setChecked(False)
        self.edit_custom.clear()
        self._on_retry_toggled(False)
        # Browser reset
        self.chk_headless.setChecked(False)
        self.chk_disable_images.setChecked(False)
        self.chk_incognito.setChecked(False)
        self.spin_w.setValue(1920)
        self.spin_h.setValue(1080)
        self.edit_ua.clear()
        self._on_headless_toggled(False)

    def _on_save(self):
        from engine.runner import get_runner_config
        from engine.browser_config import get_browser_config
        cfg = get_runner_config()
        cfg.retry_enabled    = self.chk_retry.isChecked()
        cfg.retry_attempts   = self.spin_attempts.value()
        cfg.retry_delay      = self.spin_delay.value()
        cfg.stop_on_failure  = self.chk_stop.isChecked()
        cfg.retry_on_timeout  = self._get_chk(self.chk_timeout).isChecked()
        cfg.retry_on_network  = self._get_chk(self.chk_network).isChecked()
        cfg.retry_on_stale    = self._get_chk(self.chk_stale).isChecked()
        cfg.retry_on_notfound = self._get_chk(self.chk_notfound).isChecked()
        cfg.retry_on_invalid  = self._get_chk(self.chk_invalid).isChecked()
        cfg.retry_on_custom   = self.edit_custom.text().strip()
        # Salva configurações do navegador
        bcfg = get_browser_config()
        bcfg.headless       = self.chk_headless.isChecked()
        bcfg.disable_images = self.chk_disable_images.isChecked()
        bcfg.incognito      = self.chk_incognito.isChecked()
        bcfg.window_width   = self.spin_w.value()
        bcfg.window_height  = self.spin_h.value()
        bcfg.user_agent     = self.edit_ua.text().strip()
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            #settings_title { font-size: 15px; font-weight: 700; color: #cba6f7; }
            #settings_sep { color: #313244; }
            QGroupBox {
                font-size: 13px; font-weight: 600; color: #89b4fa;
                border: 1px solid #313244; border-radius: 8px;
                margin-top: 8px; padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; left: 12px;
            }
            #settings_group_cond {
                font-size: 13px; font-weight: 600; color: #fab387;
                border: 1px solid #3a2a1c; border-radius: 8px;
                margin-top: 8px; padding-top: 14px;
                background-color: #1e1a16;
            }
            #settings_group_cond::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; left: 12px; color: #fab387;
            }
            #settings_label { font-size: 12px; color: #a6adc8; }
            #settings_nota  { font-size: 11px; color: #45475a; font-style: italic; padding-left: 4px; }
            #settings_check { font-size: 13px; color: #cdd6f4; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid #45475a; background: #313244;
            }
            QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }
            QCheckBox:disabled { color: #45475a; }
            QSpinBox, QDoubleSpinBox {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 8px; color: #cdd6f4; font-size: 12px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #cba6f7; }
            QSpinBox:disabled, QDoubleSpinBox:disabled { color: #45475a; }
            #settings_input {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 6px 10px; color: #cdd6f4; font-size: 12px;
            }
            #settings_input:focus { border-color: #fab387; }
            #btn_save {
                background-color: #cba6f7; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 7px 20px; font-weight: 700; font-size: 13px;
            }
            #btn_save:hover { background-color: #d5b8f8; }
            #btn_cancel {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 7px 16px; font-size: 13px;
            }
            #btn_cancel:hover { background-color: #45475a; }
            #btn_reset {
                background-color: transparent; color: #6c7086;
                border: none; font-size: 12px; text-decoration: underline;
            }
            #btn_reset:hover { color: #cdd6f4; }
        """)