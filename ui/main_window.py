from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel, QFileDialog,
    QMessageBox, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from ui.block_panel import BlockPanel
from ui.canvas import Canvas
from ui.properties_panel import PropertiesPanel
from ui.log_panel import LogPanel
from ui.variables_panel import VariablesPanel
from ui.command_palette import CommandPalette
from ui.debug_toolbar import DebugToolbar
from ui.templates_dialog import TemplatesDialog
from ui.flow_manager_dialog import FlowManagerDialog
from ui.scheduler_dialog import SchedulerDialog, get_signals as get_scheduler_signals
from ui.settings_dialog import SettingsDialog
from engine.runner import Runner, get_runner_config
from engine.debug_runner import DebugRunner
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
        self.flow_manager      = FlowManager()
        self.flow_exporter     = FlowExporter()
        self._scheduler_dialog = None
        self._palette          = None
        self._debug_thread     = None
        self._debug_waiting    = False
        self._build_ui()
        self._build_menu()
        self._connect_block_signals()
        self._connect_scheduler_signals()
        self._apply_styles()

    def keyPressEvent(self, event):
        key  = event.key()
        ctrl = event.modifiers() & Qt.ControlModifier
        if ctrl and key == Qt.Key_P:      self._on_open_palette(); return
        if ctrl and key == Qt.Key_S:      self._on_save();         return
        if ctrl and key == Qt.Key_Return: self._on_run();          return
        if ctrl and key == Qt.Key_L:      self._on_clear();        return
        if ctrl and key == Qt.Key_D:      self._on_debug();        return
        if ctrl and key == Qt.Key_T:      self._on_open_templates(); return
        if self._debug_thread and self._debug_thread.isRunning():
            if key == Qt.Key_Space: self._on_debug_step();   return
            if key == Qt.Key_F5:   self._on_debug_resume();  return
        super().keyPressEvent(event)

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
            self.log_panel.log("info", f"⏰ Agendador iniciou: {data.get('flow_name', '')}")
            self._on_run()
        except Exception as e:
            self.log_panel.log("error", f"Erro no agendador: {str(e)}")

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
        self.btn_run.setToolTip("Executar  [Ctrl+Enter]")
        self.btn_run.clicked.connect(self._on_run)

        self.btn_debug = QPushButton("🐛  Debug")
        self.btn_debug.setObjectName("btn_debug")
        self.btn_debug.setToolTip("Debug step-by-step  [Ctrl+D]")
        self.btn_debug.clicked.connect(self._on_debug)

        self.btn_stop = QPushButton("■  Parar")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)

        self.btn_palette = QPushButton("⚡  Ctrl+P")
        self.btn_palette.setObjectName("btn_palette")
        self.btn_palette.setToolTip("Buscar blocos  [Ctrl+P]")
        self.btn_palette.clicked.connect(self._on_open_palette)

        self.btn_templates = QPushButton("📋  Templates")
        self.btn_templates.setObjectName("btn_templates")
        self.btn_templates.setToolTip("Templates de fluxos prontos  [Ctrl+T]")
        self.btn_templates.clicked.connect(self._on_open_templates)

        self.btn_scheduler = QPushButton("⏰  Agendar")
        self.btn_scheduler.setObjectName("btn_scheduler")
        self.btn_scheduler.clicked.connect(self._on_open_scheduler)

        self.btn_vars = QPushButton("⚡  Vars")
        self.btn_vars.setObjectName("btn_vars")
        self.btn_vars.setCheckable(True)
        self.btn_vars.setChecked(True)
        self.btn_vars.setToolTip("Painel de variáveis")
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

        # ── Debug toolbar ─────────────────────────────────────────────
        self.debug_toolbar = DebugToolbar()
        self.debug_toolbar.sig_step.connect(self._on_debug_step)
        self.debug_toolbar.sig_resume.connect(self._on_debug_resume)
        self.debug_toolbar.sig_stop.connect(self._on_debug_stop)
        root.addWidget(self.debug_toolbar)

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

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("log_top_sep")
        root.addWidget(sep)

        self.log_panel = LogPanel()
        root.addWidget(self.log_panel)

        self.status = QStatusBar()
        self.status.setObjectName("status_bar")
        self.setStatusBar(self.status)
        self.status.showMessage(
            "Pronto  •  Ctrl+T templates  •  Ctrl+P buscar blocos  •  Ctrl+Enter executar  •  Ctrl+D debug"
        )

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("Arquivo")
        file_menu.addAction(QAction("Templates  [Ctrl+T]",         self, triggered=self._on_open_templates))
        file_menu.addAction(QAction("Novo fluxo  [Ctrl+L]",        self, triggered=self._on_clear))
        file_menu.addAction(QAction("Salvar  [Ctrl+S]",            self, triggered=self._on_save))
        file_menu.addAction(QAction("Gerenciar fluxos",            self, triggered=self._on_open_flow_manager))
        file_menu.addAction(QAction("Exportar como .py",           self, triggered=self._on_export))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Sair",                        self, triggered=self.close))

        view_menu = menu.addMenu("Ver")
        view_menu.addAction(QAction("Buscar blocos  [Ctrl+P]",     self, triggered=self._on_open_palette))
        view_menu.addAction(QAction("Variáveis ao vivo",           self, triggered=self._on_toggle_vars))

        run_menu = menu.addMenu("Executar")
        run_menu.addAction(QAction("Executar  [Ctrl+Enter]",       self, triggered=self._on_run))
        run_menu.addAction(QAction("Debug  [Ctrl+D]",              self, triggered=self._on_debug))
        run_menu.addAction(QAction("Agendador",                    self, triggered=self._on_open_scheduler))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Configurações",                self, triggered=self._on_open_settings))

    # ── Templates ─────────────────────────────────────────────────────

    def _on_open_templates(self):
        dialog = TemplatesDialog(templates_dir="flows", parent=self)
        dialog.template_selected.connect(self._on_template_selected)
        dialog.exec()

    def _on_template_selected(self, filepath: str):
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
        steps = self.canvas.get_steps()
        if not steps:
            self.status.showMessage("Nenhum bloco no canvas."); return
        cfg = get_runner_config()
        self._set_running(True)
        self.log_panel.log_run_start(len(steps))
        if cfg.retry_enabled:
            self.log_panel.log("info", f"↻ Retry: {cfg.retry_attempts}x / {cfg.retry_delay}s")
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

    def _on_debug_ready(self, index: int, block_name: str):
        self._debug_waiting = True
        total = self._debug_thread.total if self._debug_thread else 0
        self.canvas.set_block_state(index, "running")
        self.debug_toolbar.update_state(index, total, block_name, waiting=True)
        self.log_panel.log("running", f"🐛 Passo {index + 1}: {block_name}  — pressione ⏭ Próximo")
        self.status.showMessage(f"Debug pausado: passo {index + 1} — {block_name}  •  Space=avançar")

    def _on_debug_step(self):
        if self._debug_thread and self._debug_waiting:
            self._debug_waiting = False
            self._debug_thread.step()

    def _on_debug_resume(self):
        if self._debug_thread:
            self._debug_waiting = False
            self.log_panel.log("info", "🐛 Continuando...")
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

    def _set_running(self, running: bool, debug: bool = False):
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
        self._set_running(False)
        self.log_panel.log_run_end(ok, total)
        self.status.showMessage(f"Concluído: {ok}/{total} passos.")
        self.vars_panel.stop_live()

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
        steps = self.canvas.get_serialized_steps()
        if not steps:
            self.status.showMessage("Nada para salvar."); return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar fluxo", "flows/", "JSON (*.json)")
        if path:
            self.flow_manager.save(path.split("/")[-1].replace(".json", ""), steps)
            self.status.showMessage(f"Fluxo salvo: {path}")
            self.log_panel.log("info", f"Fluxo salvo: {path}")

    def _on_clear(self):
        if QMessageBox.question(self, "Limpar canvas", "Remover todos os blocos?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
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
            #btn_vars { background-color: #1e2a1e; color: #a6e3a1; border: 1px solid #a6e3a1; }
            #btn_vars:checked { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_settings { background-color: #313244; color: #6c7086; font-size: 15px; }
            #btn_settings:hover { background-color: #45475a; color: #cdd6f4; }
            #right_panel { background-color: #181825; }
            QSplitter::handle { background-color: #313244; width: 1px; }
            #log_top_sep { color: #313244; }
            #status_bar { background-color: #181825; color: #6c7086; border-top: 1px solid #313244; font-size: 12px; }
            QScrollBar:vertical { background: #1e1e2e; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { background: #1e1e2e; height: 8px; border-radius: 4px; }
            QScrollBar::handle:horizontal { background: #45475a; border-radius: 4px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)