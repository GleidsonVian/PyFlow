from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel, QFileDialog,
    QMessageBox, QStatusBar, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction

from ui.block_panel import BlockPanel
from ui.canvas import Canvas
from ui.properties_panel import PropertiesPanel
from ui.log_panel import LogPanel
from ui.variables_panel import VariablesPanel
from ui.command_palette import CommandPalette
from ui.debug_toolbar import DebugToolbar
from ui.templates_dialog import TemplatesDialog
from ui.api_status_dialog import ApiStatusDialog
from ui.assets_dialog import AssetsDialog
from ui.flow_manager_dialog import FlowManagerDialog
from ui.scheduler_dialog import SchedulerDialog, get_signals as get_scheduler_signals
from ui.settings_dialog import SettingsDialog
from engine.runner import Runner, get_runner_config
from engine.debug_runner import DebugRunner
from engine.flow_manager import FlowManager
from engine.flow_exporter import FlowExporter
from engine.flow_validator import validate_flow
import engine.run_history as run_history
from engine.api_server import get_api_server


class RunnerThread(QThread):
    step_started = Signal(int, str)
    step_done    = Signal(int, str, bool, str)
    step_retry   = Signal(int, str, int, int)
    run_finished = Signal(int, int)

    def __init__(self, steps, start_index: int = 0):
        super().__init__()
        self.steps       = steps
        self.start_index = start_index

    def run(self):
        runner = Runner(
            on_step_start=lambda i, b: self.step_started.emit(i, b.name),
            on_step_done= lambda i, b, r: self.step_done.emit(i, b.name, True,  r.get("message", "")),
            on_step_error=lambda i, b, r: self.step_done.emit(i, b.name, False, r.get("message", "")),
            on_step_retry=lambda i, b, a, m: self.step_retry.emit(i, b.name, a, m),
            config=get_runner_config(),
        )
        results = runner.run(self.steps, start_index=self.start_index)
        ok = sum(1 for r in results if r.get("success"))
        self.run_finished.emit(ok, len(results))


class DebugSignals(QThread):
    sig_ready    = Signal(int, str)
    sig_done     = Signal(int, str, str)
    sig_error    = Signal(int, str, str)
    sig_finished = Signal(int, int)

    def __init__(self, steps):
        super().__init__()
        self.steps = steps
        self.runner = DebugRunner(
            on_step_ready =lambda i, b, p: self.sig_ready.emit(i, b.name),
            on_step_done  =lambda i, b, r: self.sig_done.emit(i, b.name, r.get("message", "")),
            on_step_error =lambda i, b, r: self.sig_error.emit(i, b.name, r.get("message", "")),
            on_finished   =lambda ok, t:   self.sig_finished.emit(ok, t),
        )

    def run(self):
        self.runner.load(self.steps)
        self.runner.start()
        if self.runner._thread:
            self.runner._thread.join()

    def step(self):   self.runner.step()
    def resume(self): self.runner.resume()
    def stop(self):   self.runner.stop()

    @property
    def current_index(self): return self.runner.current_index
    @property
    def total(self):          return self.runner.total


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFlow RPA")
        self.setMinimumSize(1280, 720)
        self.flow_manager       = FlowManager()
        self.flow_exporter      = FlowExporter()
        self._scheduler_dialog  = None
        self._api_dialog        = None
        self._palette           = None
        self._debug_thread      = None
        self._debug_waiting     = False
        self._current_flow_name = ""
        self._current_flow_path = ""
        self._unsaved_changes   = False
        self._run_start_time    = None
        self._build_ui()
        self._build_menu()
        self._connect_block_signals()
        self._connect_scheduler_signals()
        self._start_api_server()
        self._apply_styles()
        self._setup_autosave()
        self._check_autosave_recovery()

    def keyPressEvent(self, event):
        key   = event.key()
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        if ctrl and shift and key == Qt.Key_S: self._on_save_as();         return
        if ctrl and key == Qt.Key_P:           self._on_open_palette();    return
        if ctrl and key == Qt.Key_S:           self._on_save();            return
        if ctrl and key == Qt.Key_Return:      self._on_run();             return
        if ctrl and key == Qt.Key_L:           self._on_clear();           return
        if ctrl and key == Qt.Key_D:           self._on_debug();           return
        if ctrl and key == Qt.Key_T:           self._on_open_templates();  return
        if ctrl and key == Qt.Key_A:           self._on_open_assets();     return
        if self._debug_thread and self._debug_thread.isRunning():
            if key == Qt.Key_Space: self._on_debug_step();  return
            if key == Qt.Key_F5:   self._on_debug_resume(); return
        super().keyPressEvent(event)

    # ── Autosave & título ─────────────────────────────────────────────

    def _setup_autosave(self):
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)  # 30 segundos
        self._autosave_timer.timeout.connect(self._do_autosave)
        self._autosave_timer.start()

    def _do_autosave(self):
        steps = self.canvas.get_serialized_steps()
        if steps and self._unsaved_changes:
            self.flow_manager.autosave(steps)

    def _check_autosave_recovery(self):
        if not self.flow_manager.has_autosave():
            return
        reply = QMessageBox.question(
            self, "Recuperar sessão anterior",
            "Foi encontrado um autosave da última sessão.\nDeseja recuperá-lo?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                data = self.flow_manager.load_autosave()
                self.canvas.load_from_data(data.get("steps", []))
                self._mark_unsaved()
                self.status.showMessage("Sessão anterior recuperada.")
                self.log_panel.log("info", "Sessão anterior recuperada do autosave.")
            except Exception as e:
                self.log_panel.log("error", f"Erro ao recuperar autosave: {e}")
        else:
            self.flow_manager.clear_autosave()

    def _mark_unsaved(self):
        self._unsaved_changes = True
        name = self._current_flow_name or "sem título"
        self.setWindowTitle(f"● {name}  —  PyFlow RPA")

    def _mark_saved(self, name: str, path: str):
        self._current_flow_name = name
        self._current_flow_path = path
        self._unsaved_changes   = False
        self.setWindowTitle(f"{name}  —  PyFlow RPA")
        self.flow_manager.clear_autosave()

    # ── API Server ────────────────────────────────────────────────────

    def _start_api_server(self):
        api = get_api_server()
        api.set_callbacks(
            run_cb    = self._on_scheduler_trigger,   # reutiliza o mesmo callback
            stop_cb   = self._on_stop,
            flows_dir = "flows",
        )
        api.start()
        self.log_panel.log("info", f"🌐 API REST ativa em {api.url}")

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
            self._current_flow_name = name
            self.log_panel.log("info", f"▶ Iniciado: {name}")
            get_api_server().notify_started(name)
            self._on_run()
        except Exception as e:
            self.log_panel.log("error", f"Erro ao carregar fluxo: {str(e)}")

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(8)

        title = QLabel("⚡ PyFlow RPA")
        title.setObjectName("app_title")

        self.btn_run = QPushButton("▶  Executar")
        self.btn_run.setObjectName("btn_run")
        self.btn_run.setToolTip("Executar  [Ctrl+Enter]")
        self.btn_run.clicked.connect(self._on_run)

        self.btn_debug = QPushButton("🐛  Debug")
        self.btn_debug.setObjectName("btn_debug")
        self.btn_debug.setToolTip("Debug step-by-step  [Ctrl+D]")
        self.btn_debug.clicked.connect(self._on_debug)

        self.btn_stop = QPushButton("■  Parar")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)

        self.btn_api = QPushButton("🌐  API")
        self.btn_api.setObjectName("btn_api")
        self.btn_api.setToolTip(f"API REST local — {get_api_server().url}")
        self.btn_api.clicked.connect(self._on_open_api)

        self.btn_assets = QPushButton("🔑  Assets")
        self.btn_assets.setObjectName("btn_assets")
        self.btn_assets.setToolTip("Gerenciar assets e credenciais  [Ctrl+A]")
        self.btn_assets.clicked.connect(self._on_open_assets)

        self.btn_palette = QPushButton("⚡  Ctrl+P")
        self.btn_palette.setObjectName("btn_palette")
        self.btn_palette.setToolTip("Buscar blocos  [Ctrl+P]")
        self.btn_palette.clicked.connect(self._on_open_palette)

        self.btn_templates = QPushButton("📋  Templates")
        self.btn_templates.setObjectName("btn_templates")
        self.btn_templates.setToolTip("Templates  [Ctrl+T]")
        self.btn_templates.clicked.connect(self._on_open_templates)

        self.btn_scheduler = QPushButton("⏰  Agendar")
        self.btn_scheduler.setObjectName("btn_scheduler")
        self.btn_scheduler.clicked.connect(self._on_open_scheduler)

        self.btn_vars = QPushButton("⚡  Vars")
        self.btn_vars.setObjectName("btn_vars")
        self.btn_vars.setCheckable(True)
        self.btn_vars.setChecked(True)
        self.btn_vars.clicked.connect(self._on_toggle_vars)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setObjectName("btn_settings")
        self.btn_settings.setFixedWidth(36)
        self.btn_settings.clicked.connect(self._on_open_settings)

        self.btn_flows = QPushButton("📁  Fluxos")
        self.btn_flows.setObjectName("btn_secondary")
        self.btn_flows.clicked.connect(self._on_open_flow_manager)

        self.btn_save = QPushButton("💾  Salvar")
        self.btn_save.setObjectName("btn_secondary")
        self.btn_save.setToolTip("Salvar  [Ctrl+S]")
        self.btn_save.clicked.connect(self._on_save)

        self.btn_export = QPushButton("🐍  Exportar")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.clicked.connect(self._on_export)

        self.btn_clear = QPushButton("🗑  Limpar")
        self.btn_clear.setObjectName("btn_secondary")
        self.btn_clear.setToolTip("Limpar  [Ctrl+L]")
        self.btn_clear.clicked.connect(self._on_clear)

        self.lbl_retry = QLabel("↻ Retry ON")
        self.lbl_retry.setObjectName("retry_badge")
        self.lbl_retry.hide()

        tb.addWidget(title)
        tb.addWidget(self.lbl_retry)
        tb.addStretch()
        tb.addWidget(self.btn_api)
        tb.addWidget(self.btn_assets)
        tb.addWidget(self.btn_templates)
        tb.addWidget(self.btn_palette)
        tb.addWidget(self.btn_clear)
        tb.addWidget(self.btn_flows)
        tb.addWidget(self.btn_save)
        tb.addWidget(self.btn_export)
        tb.addWidget(self.btn_vars)
        tb.addWidget(self.btn_scheduler)
        tb.addWidget(self.btn_settings)
        tb.addWidget(self.btn_stop)
        tb.addWidget(self.btn_debug)
        tb.addWidget(self.btn_run)
        root.addWidget(toolbar)

        # Debug toolbar
        self.debug_toolbar = DebugToolbar()
        self.debug_toolbar.sig_step.connect(self._on_debug_step)
        self.debug_toolbar.sig_resume.connect(self._on_debug_resume)
        self.debug_toolbar.sig_stop.connect(self._on_debug_stop)
        root.addWidget(self.debug_toolbar)

        # Área principal
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
        self.canvas.block_updated.connect(self._mark_unsaved)
        self.canvas.run_from_index.connect(self._on_run_from)

        self.splitter.addWidget(self.block_panel)
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([220, 720, 280])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(2, False)

        self.log_panel = LogPanel()

        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.setObjectName("v_splitter")
        self.v_splitter.addWidget(self.splitter)
        self.v_splitter.addWidget(self.log_panel)
        self.v_splitter.setSizes([620, 180])
        self.v_splitter.setCollapsible(0, False)
        root.addWidget(self.v_splitter, 1)

        self.status = QStatusBar()
        self.status.setObjectName("status_bar")
        self.setStatusBar(self.status)
        self.status.showMessage(
            "Pronto  •  Ctrl+P buscar blocos  •  Ctrl+Enter executar  •  Ctrl+D debug  •  Ctrl+T templates"
        )

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("Arquivo")
        file_menu.addAction(QAction("Templates  [Ctrl+T]",         self, triggered=self._on_open_templates))
        file_menu.addAction(QAction("Novo fluxo  [Ctrl+L]",        self, triggered=self._on_clear))
        file_menu.addAction(QAction("Salvar  [Ctrl+S]",            self, triggered=self._on_save))
        file_menu.addAction(QAction("Salvar como  [Ctrl+Shift+S]", self, triggered=self._on_save_as))
        file_menu.addAction(QAction("Gerenciar fluxos",            self, triggered=self._on_open_flow_manager))
        file_menu.addAction(QAction("Exportar como .py",           self, triggered=self._on_export))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Sair",                        self, triggered=self.close))

        view_menu = menu.addMenu("Ver")
        view_menu.addAction(QAction("Buscar blocos  [Ctrl+P]",     self, triggered=self._on_open_palette))
        view_menu.addAction(QAction("Variáveis ao vivo",           self, triggered=self._on_toggle_vars))
        view_menu.addAction(QAction("API REST local",              self, triggered=self._on_open_api))
        view_menu.addAction(QAction("Assets e Credenciais  [Ctrl+A]", self, triggered=self._on_open_assets))

        run_menu = menu.addMenu("Executar")
        run_menu.addAction(QAction("Executar  [Ctrl+Enter]",       self, triggered=self._on_run))
        run_menu.addAction(QAction("Debug  [Ctrl+D]",              self, triggered=self._on_debug))
        run_menu.addAction(QAction("Agendador",                    self, triggered=self._on_open_scheduler))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Histórico de execuções",       self, triggered=self._on_open_history))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Configurações",                self, triggered=self._on_open_settings))

    # ── Assets ────────────────────────────────────────────────────────

    def _on_open_history(self):
        from ui.run_history_dialog import RunHistoryDialog
        dlg = RunHistoryDialog(self)
        dlg.flow_open_requested.connect(self._load_flow_from_path)
        dlg.exec()

    def _on_open_assets(self):
        dialog = AssetsDialog(self)
        dialog.exec()

    # ── API ───────────────────────────────────────────────────────────

    def _on_open_api(self):
        if self._api_dialog is None or not self._api_dialog.isVisible():
            self._api_dialog = ApiStatusDialog(get_api_server(), self)
        self._api_dialog.show()
        self._api_dialog.raise_()
        self._api_dialog.activateWindow()

    # ── Templates ─────────────────────────────────────────────────────

    def _on_open_templates(self):
        dialog = TemplatesDialog(templates_dir="flows", parent=self)
        dialog.template_selected.connect(self._on_template_selected)
        dialog.exec()

    def _on_template_selected(self, filepath):
        try:
            data = self.flow_manager.load(filepath)
            self.canvas.load_from_data(data.get("steps", []))
            name = data.get("flow_name", filepath)
            self.status.showMessage(f"Template carregado: {name}")
            self.log_panel.log("info", f"📋 Template carregado: {name}")
            self.log_panel.log("info", "💡 Edite os parâmetros antes de executar!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar o template:\n{str(e)}")

    # ── Command Palette ───────────────────────────────────────────────

    def _on_open_palette(self):
        if self._palette and self._palette.isVisible():
            self._palette.close(); return
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
            self.log_panel.log("info", f"✚ Adicionado via Ctrl+P: {block_cls.name}")

    # ── Execução normal ───────────────────────────────────────────────

    def _on_run(self):
        self._start_run(start_index=0)

    def _on_run_from(self, index: int):
        self._start_run(start_index=index)

    def _start_run(self, start_index: int = 0):
        from ui.validation_dialog import ValidationDialog
        import time as _time

        steps = self.canvas.get_steps()
        if not steps:
            self.status.showMessage("Nenhum bloco no canvas."); return

        # Validação antes de executar
        issues = validate_flow(steps)
        if issues:
            dlg = ValidationDialog(issues, self)
            dlg.exec()
            if not dlg.should_proceed():
                return

        cfg = get_runner_config()
        self._set_running(True)
        self._run_start_time = _time.time()
        run_steps = len(steps) - start_index
        self.log_panel.log_run_start(run_steps)
        if start_index > 0:
            self.log_panel.log("info", f"▶ Iniciando a partir do passo {start_index + 1}: {steps[start_index]['block_instance'].name}")
        if cfg.retry_enabled:
            self.log_panel.log("info", f"↻ Retry: {cfg.retry_attempts}x / {cfg.retry_delay}s")
        self.vars_panel.start_live()
        self.runner_thread = RunnerThread(steps, start_index=start_index)
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
            get_api_server().notify_finished(self._current_flow_name, False, "Interrompido pelo usuário")
            self._set_running(False)
            self.vars_panel.stop_live()

    # ── Modo debug ────────────────────────────────────────────────────

    def _on_debug(self):
        steps = self.canvas.get_steps()
        if not steps:
            self.status.showMessage("Nenhum bloco no canvas."); return
        self._set_running(True, debug=True)
        self.canvas.reset_block_states()
        self.debug_toolbar.show()
        self.debug_toolbar.update_state(0, len(steps), steps[0]["block_instance"].name, True)
        self.log_panel.log("info", f"🐛 Debug iniciado — {len(steps)} blocos  •  Space=próximo  F5=continuar")
        self.vars_panel.start_live()
        self._debug_thread = DebugSignals(steps)
        self._debug_thread.sig_ready.connect(self._on_debug_ready)
        self._debug_thread.sig_done.connect(self._on_debug_done)
        self._debug_thread.sig_error.connect(self._on_debug_error)
        self._debug_thread.sig_finished.connect(self._on_debug_finished)
        self._debug_thread.start()

    def _on_debug_ready(self, index, block_name):
        self._debug_waiting = True
        total = self._debug_thread.total if self._debug_thread else 0
        self.canvas.set_block_state(index, "running")
        self.debug_toolbar.update_state(index, total, block_name, waiting=True)
        self.log_panel.log("running", f"🐛 Passo {index + 1}: {block_name}  — pressione ⏭ Próximo")

    def _on_debug_step(self):
        if self._debug_thread and self._debug_waiting:
            self._debug_waiting = False
            self._debug_thread.step()

    def _on_debug_resume(self):
        if self._debug_thread:
            self._debug_waiting = False
            self._debug_thread.resume()

    def _on_debug_stop(self):
        if self._debug_thread:
            self._debug_thread.stop()

    def _on_debug_done(self, index, block_name, message):
        self.canvas.set_block_state(index, "success")
        self.log_panel.log("success", f"✓ {block_name}: {message}")

    def _on_debug_error(self, index, block_name, message):
        self.canvas.set_block_state(index, "error")
        self.log_panel.log("error", f"✗ {block_name}: {message}")

    def _on_debug_finished(self, ok, total):
        self._set_running(False, debug=True)
        self.debug_toolbar.set_finished(ok, total)
        self.log_panel.log_run_end(ok, total)
        self.vars_panel.stop_live()
        self._debug_thread = None

    def _set_running(self, running, debug=False):
        self.btn_run.setEnabled(not running)
        self.btn_debug.setEnabled(not running)
        self.btn_stop.setEnabled(running and not debug)
        if not running:
            self.debug_toolbar.hide()

    # ── Callbacks execução normal ─────────────────────────────────────

    def _on_step_started(self, index, name):
        self.canvas.set_block_state(index, "running")
        self.status.showMessage(f"Passo {index + 1}: {name}...")
        self.log_panel.log("running", f"Passo {index + 1}: {name}")

    def _on_step_retry(self, index, name, attempt, max_attempts):
        self.log_panel.log("running", f"↻ Retry {attempt}/{max_attempts}: {name}")

    def _on_step_done(self, index, name, success, message):
        self.canvas.set_block_state(index, "success" if success else "error")
        self.log_panel.log("success" if success else "error", message or name)

    def _on_run_finished(self, ok, total):
        import time as _time
        self._set_running(False)
        self.log_panel.log_run_end(ok, total)
        self.status.showMessage(f"Concluído: {ok}/{total} passos.")
        self.vars_panel.stop_live()
        get_api_server().notify_finished(
            self._current_flow_name, ok == total,
            f"{ok}/{total} passos com sucesso"
        )
        duration = _time.time() - (self._run_start_time or _time.time())
        from datetime import datetime
        run_history.record(
            self._current_flow_name, self._current_flow_path,
            ok, total, duration,
            datetime.fromtimestamp(self._run_start_time or _time.time()).isoformat(),
        )

    # ── Outros handlers ───────────────────────────────────────────────

    def _on_toggle_vars(self):
        self.vars_panel.setVisible(self.btn_vars.isChecked())

    def _on_open_settings(self):
        if SettingsDialog(self).exec():
            self.lbl_retry.setVisible(get_runner_config().retry_enabled)

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
            self._mark_saved(name, filepath)
            self.status.showMessage(f"Fluxo carregado: {name}")
            self.log_panel.log("info", f"Fluxo carregado: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar:\n{str(e)}")

    def _on_export(self):
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para exportar."); return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar como Python", "exports/", "Python (*.py)")
        if not path: return
        import os
        try:
            filepath = self.flow_exporter.export(
                os.path.splitext(os.path.basename(path))[0],
                steps, output_dir=os.path.dirname(path))
            self.log_panel.log("success", f"🐍 Exportado: {filepath}")
            QMessageBox.information(self, "Exportação concluída",
                f"Script gerado!\n\n{filepath}\n\nPara executar:\n  python {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na exportação", str(e))

    def _on_save(self):
        """Salva direto se já tem caminho; caso contrário age como Salvar como."""
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para salvar."); return
        if self._current_flow_path:
            path = self.flow_manager.save(
                self._current_flow_name, steps, filepath=self._current_flow_path
            )
            self._mark_saved(self._current_flow_name, path)
            self.status.showMessage(f"Salvo: {path}")
            self.log_panel.log("info", f"Fluxo salvo: {path}")
        else:
            self._on_save_as()

    def _on_save_as(self):
        """Sempre abre o diálogo para escolher onde salvar."""
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para salvar."); return
        initial = self._current_flow_path or FlowManager.FLOWS_DIR + "/"
        path, _ = QFileDialog.getSaveFileName(self, "Salvar fluxo como", initial, "JSON (*.json)")
        if path:
            from pathlib import Path as _Path
            name = _Path(path).stem
            saved = self.flow_manager.save(name, steps, filepath=path)
            self._mark_saved(name, saved)
            self.status.showMessage(f"Fluxo salvo: {saved}")
            self.log_panel.log("info", f"Fluxo salvo: {saved}")

    def _on_clear(self):
        if QMessageBox.question(self, "Limpar canvas", "Remover todos os blocos?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.canvas.clear_canvas()
            self.props_panel.clear()
            self._current_flow_path = ""
            self._current_flow_name = ""
            self._unsaved_changes   = False
            self.setWindowTitle("PyFlow RPA")
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
            QMenuBar { background-color: #181825; color: #cdd6f4; padding: 2px; border-bottom: 1px solid #313244; }
            QMenuBar::item:selected { background-color: #313244; border-radius: 4px; }
            QMenu { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #313244; }
            #toolbar { background-color: #181825; border-bottom: 1px solid #313244; }
            #app_title { font-size: 15px; font-weight: 600; color: #cba6f7; }
            #retry_badge { font-size: 11px; font-weight: 600; color: #fab387; background-color: #2e1e0e; border: 1px solid #fab387; border-radius: 4px; padding: 2px 8px; }
            QPushButton { border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 500; }
            #btn_run { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_run:hover { background-color: #b9f0b3; }
            #btn_run:disabled { background-color: #45475a; color: #6c7086; }
            #btn_debug { background-color: #1e2a10; color: #a6e3a1; border: 1px solid #a6e3a1; }
            #btn_debug:hover { background-color: #2a3a1a; }
            #btn_debug:disabled { background-color: #45475a; color: #6c7086; border-color: #45475a; }
            #btn_stop { background-color: #f38ba8; color: #1e1e2e; }
            #btn_stop:hover { background-color: #f5a0b8; }
            #btn_stop:disabled { background-color: #45475a; color: #6c7086; }
            #btn_secondary { background-color: #313244; color: #cdd6f4; }
            #btn_secondary:hover { background-color: #45475a; }
            #btn_export { background-color: #1e3a5f; color: #89b4fa; border: 1px solid #89b4fa; }
            #btn_palette { background-color: #2a1e3f; color: #cba6f7; border: 1px solid #cba6f7; font-weight: 600; }
            #btn_palette:hover { background-color: #3a2e5f; }
            #btn_templates { background-color: #2a2010; color: #fab387; border: 1px solid #fab387; }
            #btn_templates:hover { background-color: #3a3020; }
            #btn_scheduler { background-color: #313244; color: #cdd6f4; }
            #btn_scheduler:hover { background-color: #45475a; }
            #btn_api { background-color: #1a2e40; color: #89b4fa; border: 1px solid #89b4fa; font-weight: 600; }
            #btn_api:hover { background-color: #1e3a50; }
            #btn_assets { background-color: #2a1a3f; color: #cba6f7; border: 1px solid #cba6f7; font-weight: 600; }
            #btn_assets:hover { background-color: #3a2a5f; }
            #btn_vars { background-color: #1e2a1e; color: #a6e3a1; border: 1px solid #a6e3a1; }
            #btn_vars:checked { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_settings { background-color: #313244; color: #6c7086; font-size: 15px; }
            #btn_settings:hover { background-color: #45475a; color: #cdd6f4; }
            #right_panel { background-color: #181825; }
            QSplitter::handle { background-color: #313244; width: 1px; height: 4px; }
            #v_splitter::handle { background-color: #313244; height: 4px; }
            #log_top_sep { color: #313244; }
            #status_bar { background-color: #181825; color: #6c7086; border-top: 1px solid #313244; font-size: 12px; }
            QScrollBar:vertical { background: #1e1e2e; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { background: #1e1e2e; height: 8px; border-radius: 4px; }
            QScrollBar::handle:horizontal { background: #45475a; border-radius: 4px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)