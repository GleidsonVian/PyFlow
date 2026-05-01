from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel, QFileDialog,
    QMessageBox, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from ui.block_panel import BlockPanel
from ui.canvas import Canvas
from ui.properties_panel import PropertiesPanel
from ui.log_panel import LogPanel
from ui.variables_panel import VariablesPanel
from ui.command_palette import CommandPalette
from ui.flow_manager_dialog import FlowManagerDialog
from ui.scheduler_dialog import SchedulerDialog, get_signals as get_scheduler_signals
from ui.settings_dialog import SettingsDialog
from engine.runner import Runner, get_runner_config
from engine.flow_manager import FlowManager
from engine.flow_exporter import FlowExporter


class RunnerThread(QThread):
    step_started = Signal(int, str)
    step_done    = Signal(int, str, bool, str)
    step_retry   = Signal(int, str, int, int)
    run_finished = Signal(int, int)

    def __init__(self, steps):
        super().__init__()
        self.steps = steps

    def run(self):
        runner = Runner(
            on_step_start=lambda i, b: self.step_started.emit(i, b.name),
            on_step_done= lambda i, b, r: self.step_done.emit(i, b.name, True,  r.get("message", "")),
            on_step_error=lambda i, b, r: self.step_done.emit(i, b.name, False, r.get("message", "")),
            on_step_retry=lambda i, b, a, m: self.step_retry.emit(i, b.name, a, m),
            config=get_runner_config(),
        )
        results = runner.run(self.steps)
        ok = sum(1 for r in results if r.get("success"))
        self.run_finished.emit(ok, len(results))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFlow RPA")
        self.setMinimumSize(1280, 720)
        self.flow_manager      = FlowManager()
        self.flow_exporter     = FlowExporter()
        self._scheduler_dialog = None
        self._palette          = None
        self._build_ui()
        self._build_menu()
        self._connect_block_signals()
        self._connect_scheduler_signals()
        self._apply_styles()

    # ── Atalhos de teclado ────────────────────────────────────────────

    def keyPressEvent(self, event):
        """Captura atalhos globais independente do widget com foco."""
        key  = event.key()
        ctrl = event.modifiers() & Qt.ControlModifier

        if ctrl and key == Qt.Key_P:
            self._on_open_palette()
            return
        if ctrl and key == Qt.Key_S:
            self._on_save()
            return
        if ctrl and key == Qt.Key_Return:
            self._on_run()
            return
        if ctrl and key == Qt.Key_L:
            self._on_clear()
            return

        super().keyPressEvent(event)

    # ── Sinais ────────────────────────────────────────────────────────

    def _connect_block_signals(self):
        from blocks.control.show_message import get_signaller
        get_signaller().show_requested.connect(self._on_show_message)

    def _connect_scheduler_signals(self):
        get_scheduler_signals().trigger_run.connect(self._on_scheduler_trigger)

    def _on_show_message(self, title, message, kind):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        icons = {"warning": QMessageBox.Warning, "error": QMessageBox.Critical}
        box.setIcon(icons.get(kind, QMessageBox.Information))
        box.setStyleSheet("""
            QMessageBox { background-color: #1e1e2e; color: #cdd6f4; font-size: 13px; }
            QLabel { color: #cdd6f4; font-size: 13px; min-width: 320px; }
            QPushButton {
                background-color: #cba6f7; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 6px 20px; font-weight: 600;
                font-size: 13px; min-width: 80px;
            }
            QPushButton:hover { background-color: #d5b8f8; }
        """)
        box.exec()

    def _on_scheduler_trigger(self, flow_path):
        try:
            data = self.flow_manager.load(flow_path)
            self.canvas.load_from_data(data.get("steps", []))
            name = data.get("flow_name", flow_path)
            self.log_panel.log("info", f"⏰ Agendador iniciou: {name}")
            self.status.showMessage(f"Agendador executando: {name}")
            self._on_run()
        except Exception as e:
            self.log_panel.log("error", f"Erro no agendador: {str(e)}")

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(8)

        title = QLabel("⚡ PyFlow RPA")
        title.setObjectName("app_title")

        self.btn_run = QPushButton("▶  Executar")
        self.btn_run.setObjectName("btn_run")
        self.btn_run.setToolTip("Executar fluxo  [Ctrl+Enter]")
        self.btn_run.clicked.connect(self._on_run)

        self.btn_stop = QPushButton("■  Parar")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)

        self.btn_palette = QPushButton("⚡  Ctrl+P")
        self.btn_palette.setObjectName("btn_palette")
        self.btn_palette.setToolTip("Buscar blocos  [Ctrl+P]")
        self.btn_palette.clicked.connect(self._on_open_palette)

        self.btn_scheduler = QPushButton("⏰  Agendar")
        self.btn_scheduler.setObjectName("btn_scheduler")
        self.btn_scheduler.clicked.connect(self._on_open_scheduler)

        self.btn_vars = QPushButton("⚡  Variáveis")
        self.btn_vars.setObjectName("btn_vars")
        self.btn_vars.setCheckable(True)
        self.btn_vars.setChecked(True)
        self.btn_vars.setToolTip("Mostrar/ocultar painel de variáveis")
        self.btn_vars.clicked.connect(self._on_toggle_vars)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setObjectName("btn_settings")
        self.btn_settings.setFixedWidth(36)
        self.btn_settings.setToolTip("Configurações de execução")
        self.btn_settings.clicked.connect(self._on_open_settings)

        self.btn_flows = QPushButton("📁  Fluxos")
        self.btn_flows.setObjectName("btn_secondary")
        self.btn_flows.clicked.connect(self._on_open_flow_manager)

        self.btn_save = QPushButton("💾  Salvar")
        self.btn_save.setObjectName("btn_secondary")
        self.btn_save.setToolTip("Salvar fluxo  [Ctrl+S]")
        self.btn_save.clicked.connect(self._on_save)

        self.btn_export = QPushButton("🐍  Exportar .py")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.clicked.connect(self._on_export)

        self.btn_clear = QPushButton("🗑  Limpar")
        self.btn_clear.setObjectName("btn_secondary")
        self.btn_clear.setToolTip("Limpar canvas  [Ctrl+L]")
        self.btn_clear.clicked.connect(self._on_clear)

        self.lbl_retry = QLabel("↻ Retry ON")
        self.lbl_retry.setObjectName("retry_badge")
        self.lbl_retry.hide()

        tb.addWidget(title)
        tb.addWidget(self.lbl_retry)
        tb.addStretch()
        tb.addWidget(self.btn_palette)
        tb.addWidget(self.btn_clear)
        tb.addWidget(self.btn_flows)
        tb.addWidget(self.btn_save)
        tb.addWidget(self.btn_export)
        tb.addWidget(self.btn_vars)
        tb.addWidget(self.btn_scheduler)
        tb.addWidget(self.btn_settings)
        tb.addWidget(self.btn_stop)
        tb.addWidget(self.btn_run)

        root.addWidget(toolbar)

        # ── Área principal ────────────────────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("main_splitter")

        self.block_panel = BlockPanel()
        self.canvas      = Canvas()

        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.props_panel = PropertiesPanel()
        self.vars_panel  = VariablesPanel()
        self.vars_panel.setFixedWidth(280)
        self.vars_panel.setMaximumHeight(280)

        sep_mid = QFrame()
        sep_mid.setFrameShape(QFrame.HLine)
        sep_mid.setObjectName("log_top_sep")

        right_layout.addWidget(self.props_panel, 1)
        right_layout.addWidget(sep_mid)
        right_layout.addWidget(self.vars_panel)

        self.canvas.block_selected.connect(self.props_panel.show_block)
        self.canvas.canvas_clicked.connect(self.props_panel.clear)
        self.canvas.block_updated.connect(self._on_block_updated)

        self.splitter.addWidget(self.block_panel)
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([220, 720, 280])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(2, False)

        root.addWidget(self.splitter, 1)

        # ── Log ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("log_top_sep")
        root.addWidget(sep)

        self.log_panel = LogPanel()
        root.addWidget(self.log_panel)

        # ── Status bar ────────────────────────────────────────────────
        self.status = QStatusBar()
        self.status.setObjectName("status_bar")
        self.setStatusBar(self.status)
        self.status.showMessage(
            "Pronto  •  Ctrl+P buscar blocos  •  Ctrl+Enter executar  •  Ctrl+S salvar"
        )

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("Arquivo")
        file_menu.addAction(QAction("Novo fluxo  [Ctrl+L]",       self, triggered=self._on_clear))
        file_menu.addAction(QAction("Salvar  [Ctrl+S]",           self, triggered=self._on_save))
        file_menu.addAction(QAction("Gerenciar fluxos",           self, triggered=self._on_open_flow_manager))
        file_menu.addAction(QAction("Exportar como .py",          self, triggered=self._on_export))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Sair",                       self, triggered=self.close))

        view_menu = menu.addMenu("Ver")
        view_menu.addAction(QAction("Buscar blocos  [Ctrl+P]",    self, triggered=self._on_open_palette))
        view_menu.addAction(QAction("Variáveis ao vivo",          self, triggered=self._on_toggle_vars))

        run_menu = menu.addMenu("Executar")
        run_menu.addAction(QAction("Executar fluxo  [Ctrl+Enter]",self, triggered=self._on_run))
        run_menu.addAction(QAction("Agendador",                   self, triggered=self._on_open_scheduler))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Configurações",               self, triggered=self._on_open_settings))

    # ── Command Palette ───────────────────────────────────────────────

    def _on_open_palette(self):
        if self._palette and self._palette.isVisible():
            self._palette.close()
            return
        self._palette = CommandPalette(self)
        self._palette.block_selected.connect(self._on_palette_block_selected)
        self._palette.show()

    def _on_palette_block_selected(self, block_cls):
        from ui.param_dialog import ParamDialog
        block_instance = block_cls()
        default_params = {s["name"]: s.get("default", "") for s in block_cls.params_schema}
        dialog = ParamDialog(block_instance, default_params, self)
        if dialog.exec():
            self.canvas._add_block(block_instance, dialog.get_params())
            self.status.showMessage(f"Bloco adicionado: {block_cls.name}")
            self.log_panel.log("info", f"✚ Adicionado via Ctrl+P: {block_cls.name}")

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_toggle_vars(self):
        self.vars_panel.setVisible(self.btn_vars.isChecked())

    def _on_open_settings(self):
        if SettingsDialog(self).exec():
            cfg = get_runner_config()
            self.lbl_retry.setVisible(cfg.retry_enabled)

    def _on_open_scheduler(self):
        if self._scheduler_dialog is None or not self._scheduler_dialog.isVisible():
            self._scheduler_dialog = SchedulerDialog(self.flow_manager, self)
        self._scheduler_dialog.show()
        self._scheduler_dialog.raise_()
        self._scheduler_dialog.activateWindow()

    def _on_open_flow_manager(self):
        dialog = FlowManagerDialog(self.flow_manager, self)
        dialog.flow_loaded.connect(self._load_flow_from_path)
        dialog.exec()

    def _load_flow_from_path(self, filepath):
        try:
            data = self.flow_manager.load(filepath)
            self.canvas.load_from_data(data.get("steps", []))
            name = data.get("flow_name", filepath)
            self.status.showMessage(f"Fluxo carregado: {name}")
            self.log_panel.log("info", f"Fluxo carregado: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar:\n{str(e)}")

    def _on_export(self):
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar como Python", "exports/", "Python (*.py)")
        if not path:
            return
        import os
        try:
            filepath = self.flow_exporter.export(
                os.path.splitext(os.path.basename(path))[0],
                steps, output_dir=os.path.dirname(path)
            )
            self.status.showMessage(f"Exportado: {filepath}")
            self.log_panel.log("success", f"🐍 Script exportado: {filepath}")
            QMessageBox.information(self, "Exportação concluída",
                f"Script gerado!\n\n{filepath}\n\nPara executar:\n  python {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na exportação", str(e))

    def _on_run(self):
        steps = self.canvas.get_steps()
        if not steps:
            self.status.showMessage("Nenhum bloco no canvas.")
            self.log_panel.log("error", "Nenhum bloco no canvas para executar.")
            return

        cfg = get_runner_config()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.canvas.reset_block_states()
        self.status.showMessage("Executando fluxo...")
        self.log_panel.log_run_start(len(steps))

        if cfg.retry_enabled:
            self.log_panel.log("info",
                f"↻ Retry: {cfg.retry_attempts}x com {cfg.retry_delay}s de intervalo")

        self.vars_panel.start_live()

        self.runner_thread = RunnerThread(steps)
        self.runner_thread.step_started.connect(self._on_step_started)
        self.runner_thread.step_done.connect(self._on_step_done)
        self.runner_thread.step_retry.connect(self._on_step_retry)
        self.runner_thread.run_finished.connect(self._on_run_finished)
        self.btn_stop.clicked.connect(self._on_stop)
        self.runner_thread.start()

    def _on_stop(self):
        if hasattr(self, "runner_thread") and self.runner_thread.isRunning():
            self.runner_thread.terminate()
            self.log_panel.log("error", "Execução interrompida.")
            self.btn_run.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status.showMessage("Execução interrompida.")
            self.vars_panel.stop_live()

    def _on_step_started(self, index, name):
        self.canvas.set_block_state(index, "running")
        self.status.showMessage(f"Executando passo {index + 1}: {name}...")
        self.log_panel.log("running", f"Passo {index + 1}: {name}")

    def _on_step_retry(self, index, name, attempt, max_attempts):
        self.canvas.set_block_state(index, "running")
        self.log_panel.log("running", f"↻ Retry {attempt}/{max_attempts}: {name}")

    def _on_step_done(self, index, name, success, message):
        self.canvas.set_block_state(index, "success" if success else "error")
        self.log_panel.log("success" if success else "error", message or name)

    def _on_run_finished(self, ok, total):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log_panel.log_run_end(ok, total)
        self.status.showMessage(f"Concluído: {ok}/{total} passos com sucesso.")
        self.vars_panel.stop_live()

    def _on_save(self):
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para salvar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar fluxo", "flows/", "JSON (*.json)")
        if path:
            name = path.split("/")[-1].replace(".json", "")
            self.flow_manager.save(name, steps)
            self.status.showMessage(f"Fluxo salvo: {path}")
            self.log_panel.log("info", f"Fluxo salvo: {path}")

    def _on_clear(self):
        reply = QMessageBox.question(self, "Limpar canvas",
            "Remover todos os blocos?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.canvas.clear_canvas()
            self.props_panel.clear()
            self.status.showMessage("Canvas limpo.")

    def _on_block_updated(self):
        selected = self.canvas.get_selected_block()
        if selected:
            self.props_panel.show_block(selected)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e; color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif; font-size: 13px;
            }
            QMenuBar {
                background-color: #181825; color: #cdd6f4;
                padding: 2px; border-bottom: 1px solid #313244;
            }
            QMenuBar::item:selected { background-color: #313244; border-radius: 4px; }
            QMenu {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 6px; padding: 4px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #313244; }
            #toolbar { background-color: #181825; border-bottom: 1px solid #313244; }
            #app_title { font-size: 15px; font-weight: 600; color: #cba6f7; }
            #retry_badge {
                font-size: 11px; font-weight: 600; color: #fab387;
                background-color: #2e1e0e; border: 1px solid #fab387;
                border-radius: 4px; padding: 2px 8px;
            }
            QPushButton {
                border: none; border-radius: 6px;
                padding: 6px 16px; font-size: 13px; font-weight: 500;
            }
            #btn_run { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_run:hover { background-color: #b9f0b3; }
            #btn_run:disabled { background-color: #45475a; color: #6c7086; }
            #btn_stop { background-color: #f38ba8; color: #1e1e2e; }
            #btn_stop:hover { background-color: #f5a0b8; }
            #btn_stop:disabled { background-color: #45475a; color: #6c7086; }
            #btn_secondary { background-color: #313244; color: #cdd6f4; }
            #btn_secondary:hover { background-color: #45475a; }
            #btn_export { background-color: #1e3a5f; color: #89b4fa; border: 1px solid #89b4fa; }
            #btn_export:hover { background-color: #1c3a5e; }
            #btn_palette { background-color: #2a1e3f; color: #cba6f7; border: 1px solid #cba6f7; font-weight: 600; }
            #btn_palette:hover { background-color: #3a2e5f; }
            #btn_scheduler { background-color: #313244; color: #cdd6f4; }
            #btn_scheduler:hover { background-color: #45475a; }
            #btn_vars { background-color: #1e2a1e; color: #a6e3a1; border: 1px solid #a6e3a1; }
            #btn_vars:hover { background-color: #2a3a2a; }
            #btn_vars:checked { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_settings { background-color: #313244; color: #6c7086; font-size: 15px; }
            #btn_settings:hover { background-color: #45475a; color: #cdd6f4; }
            #right_panel { background-color: #181825; }
            QSplitter::handle { background-color: #313244; width: 1px; }
            #log_top_sep { color: #313244; }
            #status_bar {
                background-color: #181825; color: #6c7086;
                border-top: 1px solid #313244; font-size: 12px;
            }
            QScrollBar:vertical { background: #1e1e2e; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { background: #1e1e2e; height: 8px; border-radius: 4px; }
            QScrollBar::handle:horizontal { background: #45475a; border-radius: 4px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)