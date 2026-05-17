import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel, QFileDialog,
    QMessageBox, QStatusBar, QFrame, QSizePolicy, QMenu, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence
from pathlib import Path

_ICON_PATH = Path(__file__).parent.parent / "assets" / "icon.png"

from ui.block_panel import BlockPanel
from ui.node_canvas import NodeCanvas as Canvas
from ui.properties_panel import PropertiesPanel
from ui.preview_panel import PreviewPanel
from ui.recorder_dialog import RecorderDialog
from ui.log_panel import LogPanel
from ui.help_panel import HelpPanel
from ui.variables_panel import VariablesPanel
from ui.command_palette import CommandPalette, Command
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
    step_started = Signal(int, str, str)       # index, name, category
    step_done    = Signal(int, str, str, bool, str, object)  # index, name, category, success, message, data
    step_retry   = Signal(int, str, int, int)
    run_finished = Signal(int, int, int, dict)  # ok, total, failed_idx, failed_context

    def __init__(self, steps, start_index: int = 0, graph: list = None):
        super().__init__()
        self.steps       = steps
        self.start_index = start_index
        self.graph       = graph or []

    def run(self):
        self.runner = Runner(
            on_step_start=lambda i, b: self.step_started.emit(i, b.name, getattr(b, "category", "")),
            on_step_done= lambda i, b, r: self.step_done.emit(i, b.name, getattr(b, "category", ""), True,  r.get("message", ""), r.get("data", {})),
            on_step_error=lambda i, b, r: self.step_done.emit(i, b.name, getattr(b, "category", ""), False, r.get("message", ""), r.get("data", {})),
            on_step_retry=lambda i, b, a, m: self.step_retry.emit(i, b.name, a, m),
            config=get_runner_config(),
        )
        if self.graph:
            results = self.runner.run_graph(self.graph, start_index=self.start_index)
        else:
            results = self.runner.run(self.steps, start_index=self.start_index)
            
        ok = sum(1 for r in results if r.get("success"))
        
        failed_idx = -1
        for r in results:
            if not r.get("success"):
                failed_idx = r.get("step_index", -1)
                break
                
        import engine.execution_context as context_mod
        try:
            import copy
            # Usa str() para valores complexos (como drivers ou elementos) para evitar TypeError no JSON 
            ctx_snapshot = {}
            for k, v in context_mod.get().items():
                if isinstance(v, (dict, list, str, int, float, bool, type(None))):
                    try:
                        ctx_snapshot[k] = copy.deepcopy(v)
                    except:
                        ctx_snapshot[k] = str(v)
                else:
                    ctx_snapshot[k] = str(v)
        except:
            ctx_snapshot = {k: str(v) for k, v in context_mod.get().items()}
            
        self.run_finished.emit(ok, len(results), failed_idx, ctx_snapshot)

    def stop(self):
        if hasattr(self, "runner"):
            self.runner.stop()


class DebugSignals(QThread):
    sig_ready    = Signal(int, str)
    sig_done     = Signal(int, str, str, object)
    sig_error    = Signal(int, str, str, object)
    sig_finished = Signal(int, int)

    def __init__(self, steps):
        super().__init__()
        self.steps = steps
        self.runner = DebugRunner(
            on_step_ready =lambda i, b, p: self.sig_ready.emit(i, b.name),
            on_step_done  =lambda i, b, r: self.sig_done.emit(i, b.name, r.get("message", ""), r.get("data", {})),
            on_step_error =lambda i, b, r: self.sig_error.emit(i, b.name, r.get("message", ""), r.get("data", {})),
            on_finished   =lambda ok, t:   self.sig_finished.emit(ok, t),
        )
        # IMPORTANTE: Removido parent do signaller para evitar erro de threads
        # O DebugSignals vai rodar solto na sua thread

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
    # Signals para receber chamadas da thread da API com segurança
    _api_run_signal  = Signal(str)   # flow_path
    _api_stop_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFlow RPA")
        self.setMinimumSize(1280, 720)
        if _ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self.flow_manager       = FlowManager()
        self.flow_exporter      = FlowExporter()
        self._parent_flows      = [] # Pilha para navegação de sub-processos
        self._scheduler_dialog  = None
        self._api_dialog        = None
        self._palette           = None
        self._debug_thread      = None
        self._debug_waiting     = False
        self._current_flow_name = ""
        self._current_flow_path = ""
        self._unsaved_changes   = False
        self._run_start_time    = None
        self._pending_quick_add = None
        self._build_ui()
        self._build_menu()
        self._connect_block_signals()
        self._connect_scheduler_signals()
        self._start_api_server()
        self._apply_styles()
        self._setup_autosave()
        self._check_autosave_recovery()

    def _on_compile_exe(self):
        """Chama o script de build para gerar o executável standalone."""
        from PySide6.QtWidgets import QMessageBox
        import subprocess
        import threading
        
        reply = QMessageBox.question(
            self, "Compilar Executável",
            "Deseja gerar o executável (.EXE) do PyFlow agora?\n\n"
            "Este processo pode levar de 2 a 5 minutos dependendo do seu PC.\n"
            "O PyFlow continuará funcionando, mas pode ficar lento durante o processo.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        def run_build():
            self.log_panel.log("info", "🔨 Iniciando compilação do executável... Aguarde.")
            try:
                # Chama o build.py usando o mesmo interpretador atual
                process = subprocess.Popen(
                    [sys.executable, "build.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                # Opcional: Ler saída do processo e jogar no log
                for line in process.stdout:
                    if "✅" in line or "❌" in line:
                        self.log_panel.log("info", f"Build: {line.strip()}")
                
                process.wait()
                
                if process.returncode == 0:
                    self.log_panel.log("info", "✅ Executável gerado com sucesso na pasta 'dist/PyFlowRPA'!")
                    # Abre a pasta dist no Windows Explorer
                    os.startfile(os.path.abspath("dist"))
                else:
                    self.log_panel.log("error", "❌ Falha ao compilar o executável. Verifique o console para detalhes.")
            except Exception as e:
                self.log_panel.log("error", f"❌ Erro ao disparar build: {e}")

        # Roda em uma thread separada para não travar a UI
        threading.Thread(target=run_build, daemon=True).start()

    def keyPressEvent(self, event):
        key   = event.key()
        ctrl  = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        
        if ctrl and shift and key == Qt.Key_S: self._on_save_as();         return
        if ctrl and key == Qt.Key_Z:           self.canvas.undo();         return
        if ctrl and key == Qt.Key_Y:           self.canvas.redo();         return
        if ctrl and key == Qt.Key_P:           self._on_open_palette();    return
        if ctrl and key == Qt.Key_S:           self._on_save();            return
        if ctrl and key == Qt.Key_Return:      self._on_run();             return
        if ctrl and key == Qt.Key_L:           self._on_clear();           return
        if ctrl and key == Qt.Key_D:           self._on_debug();           return
        if ctrl and key == Qt.Key_T:           self._on_open_templates();  return
        if ctrl and key == Qt.Key_A:           self._on_open_assets();     return
        if ctrl and key == Qt.Key_R:           self._on_open_recorder();   return
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
        # Conecta os signals antes de passar os callbacks para a API.
        # Signal.emit() é thread-safe — despacha para a thread principal via event loop.
        self._api_run_signal.connect(self._on_scheduler_trigger)
        self._api_stop_signal.connect(self._on_stop)

        api = get_api_server()
        api.set_callbacks(
            run_cb    = self._api_run_signal.emit,   # chamado da thread Uvicorn → signal → main thread
            stop_cb   = self._api_stop_signal.emit,  # idem
            flows_dir = "flows",
        )
        api.start()
        self.log_panel.log("info", f"🌐 API REST ativa em {api.url}")

    # ── Sinais ────────────────────────────────────────────────────────

    def _connect_block_signals(self):
        from blocks.control.show_message import get_signaller
        get_signaller().show_requested.connect(self._on_show_message)
        
        from blocks.control.input_block import get_input_signaller
        get_input_signaller().input_requested.connect(self._on_request_input_v2)

    def _connect_scheduler_signals(self):
        get_scheduler_signals().trigger_run.connect(self._on_scheduler_trigger)

    @Slot(str, str, str)
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

    @Slot(str, str, str, object)
    def _on_request_input_v2(self, title, label, default, result_obj):
        """Abre QInputDialog e sinaliza o objeto ao terminar."""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, title, label, text=default)
        
        if ok:
            result_obj.text = text
        else:
            result_obj.text = None
            
        result_obj.event.set()
        print(f"[DEBUG] Input concluído. OK: {ok}, Valor: {text}")

    def _on_scheduler_trigger(self, flow_path):
        try:
            data = self.flow_manager.load(flow_path)
            self.canvas.load_from_data(data.get("steps", []))
            name = data.get("flow_name", flow_path)
            self._current_flow_name = name
            self.log_panel.log("info", f"▶ Iniciado remotamente: {name}")
            get_api_server().notify_started(name)
            self._start_run(start_index=0, interactive=False)   # sem dialog de validação
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

        self.block_panel = BlockPanel()
        self.canvas      = Canvas()

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

        # Breadcrumbs (Navegação de Sub-processos)
        self.breadcrumb_bar = QWidget()
        self.breadcrumb_bar.setObjectName("breadcrumb_bar")
        self.breadcrumb_bar.setVisible(False)
        self.breadcrumb_bar.setStyleSheet("""
            #breadcrumb_bar { 
                background-color: #1e1e2e; 
                border-bottom: 1px solid #313244;
                min-height: 40px;
            }
            QLabel { color: #cba6f7; font-weight: bold; font-size: 13px; min-height: 14px; }
            QPushButton { 
                background-color: #313244; 
                color: #f38ba8; 
                border-radius: 4px; 
                padding: 4px 12px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f38ba8; color: #11111b; }
        """)
        bb_layout = QHBoxLayout(self.breadcrumb_bar)
        bb_layout.setContentsMargins(15, 0, 15, 0)
        self.lbl_breadcrumb = QLabel("📍 Principal")
        bb_layout.addWidget(self.lbl_breadcrumb)
        bb_layout.addStretch()
        self.btn_back = QPushButton("⬅ Voltar ao Principal")
        self.btn_back.clicked.connect(self._on_exit_subflow)
        bb_layout.addWidget(self.btn_back)
        root.addWidget(self.breadcrumb_bar)

        # Inicializa a Palette mas não exibe ainda
        self.palette = CommandPalette(self)
        self.palette.sig_add_block.connect(self._on_palette_add_block)
        self._setup_command_palette()

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

        self.btn_headless = QPushButton("🖥  Visível")
        self.btn_headless.setObjectName("btn_headless_off")
        self.btn_headless.setCheckable(True)
        self.btn_headless.setChecked(False)
        self.btn_headless.setToolTip("Modo Headless — Chrome sem janela (para produção/servidor)")
        self.btn_headless.clicked.connect(self._on_toggle_headless)

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

        self.btn_layout = QPushButton("📐  Organizar")
        self.btn_layout.setObjectName("btn_secondary")
        self.btn_layout.setToolTip("Organizar nós automaticamente")

        self.btn_record = QPushButton("⏺  Gravar")
        self.btn_record.setObjectName("btn_record")
        self.btn_record.setToolTip("Gravar ações do navegador e gerar blocos automaticamente  [Ctrl+R]")
        self.btn_record.clicked.connect(self._on_open_recorder)

        self.btn_clear = QPushButton("🗑  Limpar")
        self.btn_clear.setObjectName("btn_secondary")
        self.btn_clear.setToolTip("Limpar  [Ctrl+L]")
        self.btn_clear.clicked.connect(self._on_clear)

        self.lbl_retry = QLabel("↻ Retry ON")
        self.lbl_retry.setObjectName("retry_badge")
        self.lbl_retry.hide()

        # Menu secundário "Mais"
        self.btn_more = QPushButton("⋯")
        self.btn_more.setObjectName("btn_more")
        self.btn_more.setFixedWidth(38)
        self.btn_more.setToolTip("Mais ferramentas")

        more_menu = QMenu(self)
        more_menu.setStyleSheet("""
            QMenu { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 8px 32px; color: #cdd6f4; font-size: 13px; border-radius: 4px; }
            QMenu::item:selected { background-color: #313244; color: #cba6f7; }
            QMenu::separator { height: 1px; background: #313244; margin: 5px 0; }
        """)

        # Adiciona ações ao menu mapeando para os botões existentes
        def _add_to_menu(label, icon_text, slot):
            act = more_menu.addAction(f"{icon_text}  {label}")
            act.triggered.connect(slot)
            return act

        _add_to_menu("Busca / Paleta", "⚡", self._on_open_palette)
        _add_to_menu("Organizar Fluxo", "📐", self.canvas.auto_layout)
        _add_to_menu("Gravar Ações", "⏺", self._on_open_recorder)
        _add_to_menu("Limpar Canvas", "🗑", self._on_clear)
        more_menu.addSeparator()
        _add_to_menu("Gerenciar Fluxos", "📁", self._on_open_flow_manager)
        _add_to_menu("Exportar Python", "🐍", self._on_export)
        more_menu.addSeparator()
        _add_to_menu("Assets / Senhas", "🔑", self._on_open_assets)
        _add_to_menu("Templates", "📋", self._on_open_templates)
        _add_to_menu("Agendador", "⏰", self._on_open_scheduler)
        more_menu.addSeparator()
        
        # Checkboxes no menu para Headless e Variáveis
        act_vars = more_menu.addAction("📊 Ver Variáveis")
        act_vars.setCheckable(True)
        act_vars.setChecked(True)
        act_vars.triggered.connect(self._on_toggle_vars)
        self._act_vars = act_vars # Guarda ref se precisar sincronizar

        act_head = more_menu.addAction("🖥 Ver Navegador")
        act_head.setCheckable(True)
        act_head.setChecked(True)
        act_head.triggered.connect(self._on_toggle_headless)
        
        more_menu.addSeparator()
        _add_to_menu("Status da API", "🌐", self._on_open_api)
        _add_to_menu("Configurações", "⚙", self._on_open_settings)

        self.btn_more.setMenu(more_menu)

        # Layout final da Toolbar
        self.btn_toggle_blocks = QPushButton("≡")
        self.btn_toggle_blocks.setObjectName("btn_toggle_sidebar")
        self.btn_toggle_blocks.setToolTip("Mostrar/Esconder Blocos [Ctrl+B]")
        self.btn_toggle_blocks.setFixedWidth(40)
        self.btn_toggle_blocks.clicked.connect(self._toggle_block_panel)
        
        tb.addWidget(self.btn_toggle_blocks)
        tb.addWidget(title)
        tb.addWidget(self.lbl_retry)
        tb.addStretch()
        tb.addWidget(self.btn_run)
        tb.addWidget(self.btn_debug)
        tb.addWidget(self.btn_stop)
        tb.addSpacing(10)
        tb.addWidget(self.btn_more)
        tb.addWidget(self.btn_save)
        
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setObjectName("toolbar_sep")
        tb.addWidget(sep_v)

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

        # Painel Inspetor Contextual (Tabs)
        self.right_tabs = QTabWidget()
        self.right_tabs.setObjectName("right_tabs")
        self.right_tabs.setMinimumWidth(260)

        self.props_panel   = PropertiesPanel()
        self.preview_panel = PreviewPanel()
        self.vars_panel    = VariablesPanel()
        self.log_panel     = LogPanel()
        self.help_panel    = HelpPanel()

        self.right_tabs.addTab(self.props_panel, "⚙ Props")
        self.right_tabs.addTab(self.preview_panel, "👁 Preview")
        self.right_tabs.addTab(self.vars_panel, "𝑥 Vars")
        self.right_tabs.addTab(self.log_panel, "📜 Logs")
        self.right_tabs.addTab(self.help_panel, "❓ Ajuda")

        self.canvas.block_selected.connect(self.props_panel.show_block)
        self.canvas.block_selected.connect(self.preview_panel.show_block)
        self.canvas.block_selected.connect(self.help_panel.show_block)
        self.canvas.canvas_clicked.connect(self.props_panel.clear)
        self.canvas.canvas_clicked.connect(self.preview_panel.clear)
        self.canvas.canvas_clicked.connect(self.help_panel.clear)
        
        self.canvas.block_updated.connect(self._on_block_updated)
        self.canvas.block_updated.connect(self._mark_unsaved)
        self.canvas.run_from_index.connect(self._on_run_from)
        self.canvas.request_save.connect(self._on_save)
        self.btn_layout.clicked.connect(self.canvas.auto_layout)
        
        # Undo/Redo: salva histórico antes de aplicar edição de parâmetros
        self.props_panel.params_about_to_change.connect(self.canvas._push_history)

        self.splitter.addWidget(self.block_panel)
        self.splitter.addWidget(self.canvas)
        self.canvas.scene.sig_quick_add.connect(self._on_quick_add)
        self.canvas.request_enter_subflow.connect(self._on_enter_subflow)
        self.splitter.addWidget(self.right_tabs)
        self.splitter.setSizes([220, 780, 320])
        self.splitter.setCollapsible(0, True)
        # Permite colapsar o painel direito (agora feito via atalho)
        self.splitter.setCollapsible(2, True)

        root.addWidget(self.splitter, 1)

        # Atalhos para esconder/mostrar barras laterais
        self.shortcut_toggle_blocks = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_toggle_blocks.activated.connect(self._toggle_block_panel)
        
        self.shortcut_toggle_inspector = QShortcut(QKeySequence("Ctrl+I"), self)
        self.shortcut_toggle_inspector.activated.connect(self._toggle_right_panel)

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
        file_menu.addAction(QAction("📦 Compilar para .EXE",       self, triggered=self._on_compile_exe))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Sair",                        self, triggered=self.close))

        edit_menu = menu.addMenu("Editar")
        edit_menu.addAction(QAction("Desfazer  [Ctrl+Z]", self, triggered=self.canvas.undo))
        edit_menu.addAction(QAction("Refazer   [Ctrl+Y]", self, triggered=self.canvas.redo))

        view_menu = menu.addMenu("Ver")
        view_menu.addAction(QAction("Buscar blocos  [Ctrl+P]",     self, triggered=self._on_open_palette))
        view_menu.addAction(QAction("Variáveis ao vivo",           self, triggered=self._on_toggle_vars))
        view_menu.addAction(QAction("API REST local",              self, triggered=self._on_open_api))
        view_menu.addAction(QAction("Assets e Credenciais  [Ctrl+A]", self, triggered=self._on_open_assets))

        run_menu = menu.addMenu("Executar")
        run_menu.addAction(QAction("Executar  [Ctrl+Enter]",       self, triggered=self._on_run))
        run_menu.addAction(QAction("Debug  [Ctrl+D]",              self, triggered=self._on_debug))
        run_menu.addAction(QAction("Agendador",                    self, triggered=self._on_open_scheduler))
        run_menu.addAction(QAction("Serviço PyFlow (Daemon)",      self, triggered=self._on_open_daemon))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Histórico de execuções",       self, triggered=self._on_open_history))
        run_menu.addSeparator()
        run_menu.addAction(QAction("Configurações",                self, triggered=self._on_open_settings))

    def _toggle_block_panel(self):
        """Alterna a visibilidade do painel esquerdo (Blocos)."""
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            self._last_block_size = sizes[0]
            self.splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])
        else:
            size = getattr(self, "_last_block_size", 220)
            self.splitter.setSizes([size, sizes[1] - size, sizes[2]])

    def _toggle_right_panel(self):
        """Alterna a visibilidade do painel direito (Inspetor)."""
        sizes = self.splitter.sizes()
        if sizes[2] > 0:
            self._last_right_size = sizes[2]
            self.splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
        else:
            size = getattr(self, "_last_right_size", 320)
            self.splitter.setSizes([sizes[0], sizes[1] - size, size])


    # ── Assets ────────────────────────────────────────────────────────

    def _on_open_daemon(self):
        from ui.daemon_dialog import DaemonDialog
        dlg = DaemonDialog(self)
        dlg.exec()

    def _on_open_history(self):
        from ui.run_history_dialog import RunHistoryDialog
        dlg = RunHistoryDialog(self)
        dlg.flow_open_requested.connect(self._load_flow_from_path)
        dlg.resume_run_requested.connect(self._resume_run)
        dlg.exec()

    def _resume_run(self, path: str, failed_idx: int, ctx_snapshot: dict):
        try:
            # Carrega o fluxo
            data = self.flow_manager.load(path)
            self.canvas.load_from_data(data.get("steps", []))
            name = data.get("flow_name", path)
            self._mark_saved(name, path)
            
            # Restaura o snapshot das variáveis para que a execução continue com o estado antigo
            import engine.execution_context as context_mod
            context_mod.clear()
            if isinstance(ctx_snapshot, dict):
                context_mod.get().update(ctx_snapshot)
                
            self.status.showMessage(f"Retomando {name} do passo {failed_idx + 1}")
            self.log_panel.log("info", f"⏪ Retomando execução do fluxo {name} a partir do passo {failed_idx + 1}")
            
            # Inicia do ponto de falha
            self._start_run(start_index=failed_idx, interactive=True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro ao retomar", f"Não foi possível retomar o fluxo:\n{str(e)}")

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

    def _on_open_recorder(self):
        """Abre o Macro Recorder para gravar ações do Chrome e gerar blocos."""
        dialog = RecorderDialog(parent=self)
        dialog.steps_ready.connect(self._on_recorder_steps_ready)
        dialog.exec()

    def _on_recorder_steps_ready(self, steps: list):
        """Recebe os steps gravados e adiciona ao canvas."""
        if not steps:
            return
        current = self.canvas.get_serialized_steps()
        all_steps = current + steps
        self.canvas.load_from_data(all_steps)
        self.log_panel.log(
            "info",
            f"⏺ Macro Recorder: {len(steps)} bloco(s) adicionado(s) ao canvas."
        )
        self.status.showMessage(f"Gravação concluída — {len(steps)} bloco(s) adicionado(s)")

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
        self.palette.show()

    # ── Execução normal ───────────────────────────────────────────────

    def _on_run(self):
        self._start_run(start_index=0, interactive=True)

    def _on_run_from(self, index: int):
        self._start_run(start_index=index, interactive=True)

    def _start_run(self, start_index: int = 0, interactive: bool = True):
        from ui.validation_dialog import ValidationDialog
        import time as _time

        steps = self.canvas.get_steps()
        if not steps:
            self.status.showMessage("Nenhum bloco no canvas."); return

        # Validação antes de executar
        issues = validate_flow(steps)
        if issues:
            if interactive:
                # Execução manual: mostra dialog e aguarda confirmação
                dlg = ValidationDialog(issues, self)
                dlg.exec()
                if not dlg.should_proceed():
                    return
            else:
                # Execução remota (API/agendador): apenas loga, nunca bloqueia
                errors   = [x for x in issues if x["level"] == "error"]
                warnings = [x for x in issues if x["level"] == "warning"]
                for w in warnings:
                    self.log_panel.log("warning", f"⚠ Passo {w['step']} — {w['block']}: {w['msg']}")
                if errors:
                    for e in errors:
                        self.log_panel.log("error", f"✗ Passo {e['step']} — {e['block']}: {e['msg']}")
                    self.log_panel.log("error", "Execução remota cancelada: erros de validação impedem a execução.")
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
        graph = self.canvas.get_graph()
        self.runner_thread = RunnerThread(steps, start_index=start_index, graph=graph)
        self.runner_thread.step_started.connect(self._on_step_started)
        self.runner_thread.step_done.connect(self._on_step_done)
        self.runner_thread.step_retry.connect(self._on_step_retry)
        self.runner_thread.run_finished.connect(self._on_run_finished)
        self.btn_stop.clicked.connect(self._on_stop)
        self.runner_thread.start()

    def _on_stop(self):
        if hasattr(self, "runner_thread") and self.runner_thread.isRunning():
            self.runner_thread.stop()
            self.log_panel.log("warning", "Solicitando parada... aguardando passo atual finalizar.")
            # Não chamamos _set_running(False) aqui, o sinal run_finished cuidará disso ao terminar

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

    def _on_debug_done(self, index, block_name, message, data=None):
        self.canvas.set_block_state(index, "success")
        self.canvas.set_block_result(index, message, True, data=data)
        self.log_panel.log("success", f"✓ {block_name}: {message}")

    def _on_debug_error(self, index, block_name, message, data=None):
        self.canvas.set_block_state(index, "error")
        self.canvas.set_block_result(index, message, False, data=data)
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

    def _on_step_started(self, index, name, category=""):
        self._step_start_time = time.time() # Registra o início do passo
        self.canvas.set_block_state(index, "running")
        self.status.showMessage(f"Passo {index + 1}: {name}...")
        self.log_panel.log("running", f"Passo {index + 1}: {name}", step=index + 1, block_name=name, category=category)

    def _on_step_retry(self, index, name, attempt, max_attempts):
        self.log_panel.log("warning", f"↻ Retry {attempt}/{max_attempts}: {name}")

    def _on_step_done(self, index, name, category, success, message, data=None):
        duration = time.time() - getattr(self, "_step_start_time", time.time())
        self.canvas.set_block_state(index, "success" if success else "error")
        self.canvas.set_block_result(index, message, success, duration=duration, data=data)
        self.log_panel.log(
            "success" if success else "error",
            message or name,
            step=index + 1,
            block_name=name,
            category=category,
        )

    def _on_run_finished(self, ok, total, failed_idx=-1, failed_context=None):
        self._set_running(False)
        self.log_panel.log_run_end(ok, total)
        self.status.showMessage(f"Concluído: {ok}/{total} passos.")
        self.vars_panel.stop_live()
        get_api_server().notify_finished(
            self._current_flow_name, ok == total,
            f"{ok}/{total} passos com sucesso"
        )
        duration = time.time() - (self._run_start_time or time.time())
        from datetime import datetime
        run_history.record(
            self._current_flow_name, self._current_flow_path,
            ok, total, duration,
            datetime.fromtimestamp(self._run_start_time or time.time()).isoformat(),
            failed_idx, failed_context or {}
        )

    # ── Outros handlers ───────────────────────────────────────────────

    def _on_toggle_vars(self):
        self.vars_panel.setVisible(self.btn_vars.isChecked())

    def _on_toggle_headless(self):
        from engine.browser_config import get_browser_config
        cfg = get_browser_config()
        cfg.headless = self.btn_headless.isChecked()
        if cfg.headless:
            self.btn_headless.setText("👻  Headless")
            self.btn_headless.setObjectName("btn_headless_on")
            self.log_panel.log("info", "👻 Modo Headless ATIVADO — Chrome rodará sem janela")
        else:
            self.btn_headless.setText("🖥  Visível")
            self.btn_headless.setObjectName("btn_headless_off")
            self.log_panel.log("info", "🖥  Modo Visível ATIVADO — Chrome abrirá com janela")
        # Força reaplicação do estilo
        self.btn_headless.style().unpolish(self.btn_headless)
        self.btn_headless.style().polish(self.btn_headless)

    # ── Navegação de Sub-processos ────────────────────────────────────

    def _on_enter_subflow(self, node):
        """Entra no sub-processo para edição inline."""
        # Se não tiver dados internos, inicializa
        internal = node.params.get("_internal_steps", [])
        
        # Salva o estado atual
        current_state = self.canvas.get_serialized_steps()
        self._parent_flows.append({
            "state": current_state,
            "node_id": node.node_id,
            "name": node.params.get("flow_name", "Subfluxo")
        })
        
        # Carrega o subfluxo
        self.canvas.load_from_serialized_steps(internal)
        
        # Atualiza UI
        self.breadcrumb_bar.setVisible(True)
        path_str = " > ".join(["Principal"] + [f["name"] for f in self._parent_flows])
        self.lbl_breadcrumb.setText(f"📍 {path_str}")
        self.status.showMessage(f"Editando sub-processo: {node.params.get('flow_name', 'Sem nome')}")

    def _on_exit_subflow(self):
        """Volta para o nível superior."""
        if not self._parent_flows:
            return
            
        # Salva o que foi feito no subfluxo
        sub_state = self.canvas.get_serialized_steps()
        
        # Recupera o pai
        parent = self._parent_flows.pop()
        self.canvas.load_from_serialized_steps(parent["state"])
        
        # Atualiza o nó do subfluxo no pai com os novos passos
        # Nota: precisamos achar o nó novamente pois o canvas foi recarregado
        target_node = next((n for n in self.canvas.scene._nodes if n.node_id == parent["node_id"]), None)
        if target_node:
            target_node.params["_internal_steps"] = sub_state
        
        # Atualiza UI
        if not self._parent_flows:
            self.breadcrumb_bar.setVisible(False)
        else:
            path_str = " > ".join(["Principal"] + [f["name"] for f in self._parent_flows])
            self.lbl_breadcrumb.setText(f"📍 {path_str}")
        
        self.status.showMessage("De volta ao fluxo principal.")

    def _on_open_settings(self):
        if SettingsDialog(self).exec():
            self.lbl_retry.setVisible(get_runner_config().retry_enabled)
            # Sincroniza botão headless com o valor salvo nas configurações
            from engine.browser_config import get_browser_config
            is_headless = get_browser_config().headless
            self.btn_headless.blockSignals(True)
            self.btn_headless.setChecked(is_headless)
            self.btn_headless.blockSignals(False)
            if is_headless:
                self.btn_headless.setText("👻  Headless")
                self.btn_headless.setObjectName("btn_headless_on")
            else:
                self.btn_headless.setText("🖥  Visível")
                self.btn_headless.setObjectName("btn_headless_off")
            self.btn_headless.style().unpolish(self.btn_headless)
            self.btn_headless.style().polish(self.btn_headless)

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

    def _on_palette_add_block(self, block_cls):
        if self._pending_quick_add:
            src_port  = self._pending_quick_add["src_port"]
            scene_pos = self._pending_quick_add["pos"]
            new_node = self.canvas.add_block_at_pos(block_cls, scene_pos)
            if new_node:
                self.canvas.add_connection(src_port, new_node.in_port)
            self._pending_quick_add = None
        else:
            self.canvas.add_block_at_center(block_cls)

    def _on_quick_add(self, src_port, scene_pos):
        """Abre a paleta salvando o contexto para conexão automática."""
        self._pending_quick_add = {"src_port": src_port, "pos": scene_pos}
        # Centraliza a paleta na tela (padrão) ou poderíamos mover para o mouse
        self.palette.show()
        self.palette.search.setFocus()
        self.palette.search.setText("")

    def _setup_command_palette(self):
        cmds = [
            Command("Executar Fluxo", "Ações", self._on_run, shortcut="F5"),
            Command("Debug Passo a Passo", "Ações", self._on_debug, shortcut="Ctrl+D"),
            Command("Parar Execução", "Ações", self._on_stop, icon="■"),
            
            Command("Salvar Fluxo", "Projeto", self._on_save, shortcut="Ctrl+S"),
            Command("Salvar Como...", "Projeto", self._on_save_as, shortcut="Ctrl+Shift+S"),
            Command("Gerenciar Fluxos", "Projeto", self._on_open_flow_manager, icon="📁"),
            Command("Exportar Python", "Projeto", self._on_export, icon="🐍"),
            
            Command("Organizar Canvas", "Navegação", self.canvas.auto_layout, icon="📐"),
            Command("Limpar Canvas", "Navegação", self._on_clear, icon="🗑"),
            Command("Adicionar Comentário", "Navegação", self.canvas.add_comment_at_center, icon="📝"),
            Command("Alinhar ao Topo", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("top"), shortcut="Ctrl+Shift+Up"),
            Command("Alinhar à Base", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("bottom"), shortcut="Ctrl+Shift+Down"),
            Command("Alinhar à Esquerda", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("left"), shortcut="Ctrl+Shift+Left"),
            Command("Alinhar à Direita", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("right"), shortcut="Ctrl+Shift+Right"),
            Command("Centralizar H", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("center_h"), shortcut="Ctrl+Shift+C"),
            Command("Centralizar V", "Alinhamento", lambda: self.canvas.scene.align_selected_nodes("center_v"), shortcut="Ctrl+Shift+V"),

            
            Command("Assets / Senhas", "Gestão", self._on_open_assets, shortcut="Ctrl+A"),
            Command("Templates", "Gestão", self._on_open_templates, shortcut="Ctrl+T"),
            Command("Agendador / Cron", "Gestão", self._on_open_scheduler, icon="⏰"),
            Command("Status da API", "Gestão", self._on_open_api, icon="🌐"),
            Command("Configurações", "Gestão", self._on_open_settings, icon="⚙"),

            Command("Ver Variáveis", "Visual", self._on_toggle_vars, icon="📊"),
            Command("Ver Navegador", "Visual", self._on_toggle_headless, icon="🖥"),
        ]
        self.palette.register_commands(cmds)

    def _apply_styles(self):
        import engine.theme_manager as tm
        self.setStyleSheet(tm.build_main_qss())
