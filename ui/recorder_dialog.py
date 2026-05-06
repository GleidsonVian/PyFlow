"""
RecorderDialog — janela flutuante do Macro Recorder.

Fluxo do clique direito:
  1. JS no Chrome captura o evento e envia 'context_menu_request' ao Python.
  2. RecorderDialog recebe o sinal e exibe um QMenu NATIVO (fora do Chrome).
  3. Usuário escolhe a ação no menu Qt → bloco registrado na lista.

Isso elimina qualquer interferência de eventos dentro do DOM do Chrome.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy, QMessageBox, QMenu,
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QCursor, QAction

from engine.macro_recorder import MacroRecorder, action_to_step, action_label


# ── Bridge thread-safe ────────────────────────────────────────────────────────

class _RecorderBridge(QObject):
    action_captured      = Signal(object)   # cliques, inputs, teclas, navegação
    context_menu_request = Signal(object)   # clique direito via pynput
    url_changed          = Signal(str)
    error_occurred       = Signal(str)


# ── Dialog ────────────────────────────────────────────────────────────────────

class RecorderDialog(QDialog):
    """
    Janela de gravação. Emite steps_ready(list) ao clicar "Adicionar ao Canvas".
    """
    steps_ready = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Macro Recorder")
        self.setMinimumWidth(500)
        self.setMinimumHeight(440)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint
        )

        self._actions: list[dict] = []
        self._recorder: MacroRecorder | None = None

        self._bridge = _RecorderBridge()
        self._bridge.action_captured.connect(self._on_action)
        self._bridge.context_menu_request.connect(self._on_context_menu_request)
        self._bridge.url_changed.connect(self._on_url_changed)
        self._bridge.error_occurred.connect(self._on_error)

        self._build_ui()
        self._apply_styles()
        self._start_recording()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Status
        header = QHBoxLayout()
        self._dot = QLabel("●")
        self._dot.setObjectName("rec_dot")
        self._lbl_status = QLabel("Gravando...  use o Chrome normalmente")
        self._lbl_status.setObjectName("rec_status")
        header.addWidget(self._dot)
        header.addWidget(self._lbl_status)
        header.addStretch()
        self._lbl_count = QLabel("0 acoes")
        self._lbl_count.setObjectName("rec_count")
        header.addWidget(self._lbl_count)
        layout.addLayout(header)

        tip = QLabel(
            "  Clique esquerdo  ->  registra automaticamente\n"
            "  Clique DIREITO   ->  abre menu para escolher o que coletar"
        )
        tip.setObjectName("rec_tip")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("rec_sep")
        layout.addWidget(sep)

        self._list = QListWidget()
        self._list.setObjectName("rec_list")
        self._list.setSelectionMode(QListWidget.SingleSelection)
        self._list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_clear = QPushButton("Limpar tudo")
        self._btn_clear.setObjectName("btn_rec_secondary")
        self._btn_clear.clicked.connect(self._on_clear)

        self._btn_remove = QPushButton("Remover selecionado")
        self._btn_remove.setObjectName("btn_rec_secondary")
        self._btn_remove.clicked.connect(self._on_remove_selected)

        self._btn_stop = QPushButton("Parar gravacao")
        self._btn_stop.setObjectName("btn_rec_stop")
        self._btn_stop.clicked.connect(self._on_stop)

        self._btn_add = QPushButton("Adicionar ao Canvas")
        self._btn_add.setObjectName("btn_rec_add")
        self._btn_add.setEnabled(False)
        self._btn_add.clicked.connect(self._on_add_to_canvas)

        btn_row.addWidget(self._btn_clear)
        btn_row.addWidget(self._btn_remove)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_stop)
        btn_row.addWidget(self._btn_add)
        layout.addLayout(btn_row)

    # ── Gravação ──────────────────────────────────────────────────────

    def _start_recording(self):
        try:
            self._recorder = MacroRecorder(
                on_action=lambda a: self._bridge.action_captured.emit(a),
                on_context_menu=lambda d: self._bridge.context_menu_request.emit(d),
                on_url_change=lambda u: self._bridge.url_changed.emit(u),
                on_error=lambda e: self._bridge.error_occurred.emit(e),
            )
            self._recorder.start()
        except RuntimeError as e:
            self._set_stopped_state()
            QMessageBox.warning(self, "Macro Recorder", str(e))

    def _on_stop(self):
        if self._recorder:
            self._recorder.stop()
            self._recorder = None
        self._set_stopped_state()

    def _set_stopped_state(self):
        self._dot.setStyleSheet("color: #6c7086; font-size: 18px;")
        self._dot.setText("■")
        self._lbl_status.setText("Gravacao encerrada")
        self._btn_stop.setEnabled(False)
        self._btn_add.setEnabled(bool(self._actions))

    # ── Menu de contexto Qt nativo (clique direito no Chrome) ─────────

    def _on_context_menu_request(self, data: dict):
        """Chamado quando pynput detecta clique direito sobre o Chrome."""
        pos = QCursor.pos()
        # Delay curto para o Chrome processar o contextmenu antes do QMenu aparecer
        QTimer.singleShot(80, lambda: self._show_context_menu(data, pos))

    def _show_context_menu(self, data: dict, pos):
        """Monta e exibe o QMenu nativo com as opções para o elemento clicado."""
        selector = data.get("selector", "")
        tag      = data.get("tag", "")
        text     = data.get("text", "")
        attrs    = data.get("attrs", [])
        is_input = tag in ("input", "textarea", "select")
        is_list  = data.get("is_list", False)

        # Força o dialog para frente e garante que o Qt receba o foco
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()
        self.raise_()
        self.activateWindow()

        menu = QMenu(self)

        # Cabeçalho informativo
        hdr = QAction(f"  {selector[:52]}", self)
        hdr.setEnabled(False)
        menu.addAction(hdr)
        menu.addSeparator()

        actions_map: dict[QAction, dict] = {}

        def add_opt(label: str, action_dict: dict) -> None:
            act = QAction(label, self)
            menu.addAction(act)
            actions_map[act] = action_dict

        add_opt("  Coletar texto do elemento",
                {"type": "extract_text", "selector": selector})

        # Atributos disponíveis no elemento (enviados pelo JS)
        for attr in attrs:
            val_preview = ""
            try:
                from blocks.browser.open_browser import OpenBrowserBlock
                from selenium.webdriver.common.by import By
                driver = OpenBrowserBlock.get_driver()
                if driver:
                    els = driver.find_elements(By.CSS_SELECTOR, selector)
                    if els:
                        v = els[0].get_attribute(attr) or ""
                        val_preview = f"   ->  {v[:35]}" if v else ""
            except Exception:
                pass
            add_opt(f"  Coletar atributo  [{attr}]{val_preview}",
                    {"type": "extract_attr", "selector": selector, "attribute": attr})

        if is_list:
            add_opt("  Extrair lista de elementos iguais",
                    {"type": "extract_list", "selector": selector})

        menu.addSeparator()

        if is_input:
            add_opt("  Preencher este campo",
                    {"type": "fill", "selector": selector, "value": ""})

        add_opt("  Clicar neste elemento",
                {"type": "click", "selector": selector, "label": text, "tag": tag})

        menu.addSeparator()

        add_opt("  Aguardar elemento aparecer",
                {"type": "smart_wait", "selector": selector})

        add_opt("  Tirar screenshot da pagina",
                {"type": "screenshot", "selector": selector})

        chosen = menu.exec(pos)
        if chosen and chosen in actions_map:
            self._on_action(actions_map[chosen])

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_action(self, action: dict):
        step = action_to_step(action)
        if step is None:
            return
        self._actions.append(action)
        item = QListWidgetItem(action_label(action))
        item.setData(Qt.UserRole, len(self._actions) - 1)
        self._list.addItem(item)
        self._list.scrollToBottom()
        n = len(self._actions)
        self._lbl_count.setText(f"{n} acao{'es' if n != 1 else ''}")
        self._btn_add.setEnabled(True)

    def _on_url_changed(self, url: str):
        self._on_action({"type": "navigate", "url": url})

    def _on_error(self, msg: str):
        self._lbl_status.setText(f"Aviso: {msg[:80]}")

    # ── Lista ─────────────────────────────────────────────────────────

    def _on_clear(self):
        self._actions.clear()
        self._list.clear()
        self._lbl_count.setText("0 acoes")
        self._btn_add.setEnabled(False)

    def _on_remove_selected(self):
        row = self._list.currentRow()
        if row < 0:
            return
        self._list.takeItem(row)
        self._actions.pop(row)
        for i in range(self._list.count()):
            self._list.item(i).setData(Qt.UserRole, i)
        n = len(self._actions)
        self._lbl_count.setText(f"{n} acoes")
        self._btn_add.setEnabled(bool(self._actions))

    def _on_add_to_canvas(self):
        steps = [s for a in self._actions if (s := action_to_step(a))]
        if steps:
            self.steps_ready.emit(steps)
            self.accept()

    # ── Fechar ────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._recorder:
            self._recorder.stop()
            self._recorder = None
        super().closeEvent(event)

    # ── Estilos ───────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }

            #rec_dot    { color: #f38ba8; font-size: 20px; font-weight: bold; }
            #rec_status { color: #cdd6f4; font-size: 13px; font-weight: 600; }
            #rec_count  { color: #6c7086; font-size: 12px; }

            #rec_tip {
                color: #585b70; font-size: 11px;
                background: #181825; border-radius: 6px;
                padding: 8px 12px;
            }

            #rec_sep { background-color: #313244; max-height: 1px; }

            #rec_list {
                background-color: #181825;
                border: 1px solid #313244; border-radius: 8px;
                color: #cdd6f4; font-size: 12px; padding: 6px; outline: none;
            }
            #rec_list::item {
                padding: 7px 10px; border-radius: 5px; margin: 1px 0;
            }
            #rec_list::item:selected { background-color: #313244; color: #cba6f7; }
            #rec_list::item:hover    { background-color: #24273a; }

            #btn_rec_stop {
                background-color: #3a1c1c; color: #f38ba8;
                border: 1px solid #f38ba8; border-radius: 7px;
                padding: 7px 18px; font-size: 13px; font-weight: 600;
            }
            #btn_rec_stop:hover    { background-color: #4a2020; }
            #btn_rec_stop:disabled { color: #6c7086; border-color: #6c7086; }

            #btn_rec_add {
                background-color: #1c3a2a; color: #a6e3a1;
                border: 1px solid #a6e3a1; border-radius: 7px;
                padding: 7px 18px; font-size: 13px; font-weight: 700;
            }
            #btn_rec_add:hover    { background-color: #1e4a30; }
            #btn_rec_add:disabled { color: #45475a; border-color: #45475a; }

            #btn_rec_secondary {
                background-color: #313244; color: #cdd6f4;
                border: none; border-radius: 7px; padding: 7px 14px; font-size: 12px;
            }
            #btn_rec_secondary:hover { background-color: #45475a; }

            QMenu {
                background-color: #1e1e2e;
                border: 1.5px solid #cba6f7;
                border-radius: 8px;
                padding: 4px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QMenu::item { padding: 8px 20px; border-radius: 5px; }
            QMenu::item:selected { background-color: #313244; color: #cba6f7; }
            QMenu::item:disabled { color: #45475a; font-size: 11px; }
            QMenu::separator { background-color: #313244; height: 1px; margin: 3px 0; }
        """)
