"""
Janela de status e documentação da API REST do PyFlow RPA.
Coloque em: ui/api_status_dialog.py
"""
import webbrowser

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QListWidget,
    QListWidgetItem, QApplication, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont


class ApiStatusDialog(QDialog):
    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.server = server
        self.setWindowTitle("🌐  API REST Local")
        self.setMinimumSize(560, 480)
        self.setModal(False)
        self._build_ui()
        self._apply_styles()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("api_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 14, 16, 14)

        title = QLabel("🌐  API REST Local")
        title.setObjectName("api_title")

        self.lbl_status = QLabel("● Ativo")
        self.lbl_status.setObjectName("api_status_on")

        self.btn_copy_url = QPushButton("⎘  Copiar URL")
        self.btn_copy_url.setObjectName("btn_api_copy")
        self.btn_copy_url.clicked.connect(self._copy_url)

        self.btn_open_dashboard = QPushButton("🖥  Abrir Dashboard")
        self.btn_open_dashboard.setObjectName("btn_api_dashboard")
        self.btn_open_dashboard.setToolTip(f"Abre {self.server.url}/dashboard no navegador")
        self.btn_open_dashboard.clicked.connect(self._open_dashboard)

        h.addWidget(title)
        h.addStretch()
        h.addWidget(self.lbl_status)
        h.addWidget(self.btn_copy_url)
        h.addWidget(self.btn_open_dashboard)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("api_sep")
        root.addWidget(sep)

        # ── Tabs ──────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setObjectName("api_tabs")

        # Tab: Endpoints
        tab_endpoints = QWidget()
        te_layout = QVBoxLayout(tab_endpoints)
        te_layout.setContentsMargins(16, 12, 16, 12)
        te_layout.setSpacing(10)

        self.lbl_url = QLabel(self.server.url)
        self.lbl_url.setObjectName("api_url")
        te_layout.addWidget(self.lbl_url)

        endpoints = [
            ("GET",  "/",           "Informações gerais da API"),
            ("GET",  "/dashboard",  "Painel web de monitoramento (abra no browser)"),
            ("GET",  "/flows",      "Lista todos os fluxos salvos"),
            ("POST", "/run",        'Executa um fluxo — body: {"flow": "nome"}'),
            ("GET",  "/status",     "Estado atual da execução"),
            ("GET",  "/history",    "Histórico das últimas execuções"),
            ("POST", "/stop",       "Para a execução atual"),
        ]

        for method, path, desc in endpoints:
            te_layout.addWidget(self._endpoint_row(method, path, desc))

        te_layout.addStretch()

        # Tab: Exemplos
        tab_examples = QWidget()
        tex_layout = QVBoxLayout(tab_examples)
        tex_layout.setContentsMargins(16, 12, 16, 12)
        tex_layout.setSpacing(8)

        examples = [
            ("Listar fluxos", f"curl {self.server.url}/flows"),
            ("Disparar fluxo", f'curl -X POST {self.server.url}/run \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"flow": "meu_fluxo"}}\''),
            ("Ver status", f"curl {self.server.url}/status"),
            ("Histórico", f"curl {self.server.url}/history?limit=10"),
            ("Parar execução", f"curl -X POST {self.server.url}/stop"),
            ("Python requests", f'import requests\nrequests.post("{self.server.url}/run",\n  json={{"flow": "scraping"}})'),
        ]

        for title, code in examples:
            tex_layout.addWidget(self._example_block(title, code))

        tex_layout.addStretch()

        # Tab: Histórico
        tab_history = QWidget()
        th_layout = QVBoxLayout(tab_history)
        th_layout.setContentsMargins(0, 0, 0, 0)

        self.history_list = QListWidget()
        self.history_list.setObjectName("api_history_list")
        th_layout.addWidget(self.history_list)

        tabs.addTab(tab_endpoints, "📡  Endpoints")
        tabs.addTab(tab_examples,  "💡  Exemplos")
        tabs.addTab(tab_history,   "📋  Histórico")
        root.addWidget(tabs, 1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("api_sep")
        root.addWidget(sep2)

        # Footer
        footer = QWidget()
        footer.setObjectName("api_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(16, 10, 16, 10)

        self.lbl_current = QLabel("Idle — nenhum fluxo em execução")
        self.lbl_current.setObjectName("api_current")

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_api_close")
        btn_close.clicked.connect(self.close)

        f.addWidget(self.lbl_current, 1)
        f.addWidget(btn_close)
        root.addWidget(footer)

    def _endpoint_row(self, method: str, path: str, desc: str) -> QWidget:
        w = QWidget()
        w.setObjectName("endpoint_row")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        method_colors = {"GET": "#a6e3a1", "POST": "#fab387"}
        color = method_colors.get(method, "#89b4fa")

        lbl_method = QLabel(method)
        lbl_method.setObjectName("endpoint_method")
        lbl_method.setStyleSheet(f"color: {color}; background: transparent;")
        lbl_method.setFixedWidth(42)

        lbl_path = QLabel(path)
        lbl_path.setObjectName("endpoint_path")
        lbl_path.setFixedWidth(100)

        lbl_desc = QLabel(desc)
        lbl_desc.setObjectName("endpoint_desc")

        btn_copy = QLabel("⎘")
        btn_copy.setObjectName("endpoint_copy")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setToolTip("Copiar URL completa")
        full_url = f"{self.server.url}{path}"
        btn_copy.mousePressEvent = lambda e, u=full_url: QApplication.clipboard().setText(u)

        layout.addWidget(lbl_method)
        layout.addWidget(lbl_path)
        layout.addWidget(lbl_desc, 1)
        layout.addWidget(btn_copy)
        return w

    def _example_block(self, title: str, code: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("example_title")

        lbl_code = QLabel(code)
        lbl_code.setObjectName("example_code")
        lbl_code.setWordWrap(True)
        lbl_code.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_code)
        return w

    def _refresh(self):
        from engine.api_server import _state

        active = self.server.is_active
        self.lbl_status.setText("● Ativo" if active else "○ Inativo")
        self.lbl_status.setObjectName("api_status_on" if active else "api_status_off")

        if _state["running"]:
            self.lbl_current.setText(f"▶ Executando: {_state['current_flow']}")
        else:
            self.lbl_current.setText("Idle — nenhum fluxo em execução")

        # Atualiza histórico
        self.history_list.clear()
        for entry in _state["history"]:
            icon  = "✓" if entry["success"] else "✗"
            color = "#a6e3a1" if entry["success"] else "#f38ba8"
            text  = f"  {icon}  {entry['timestamp']}  {entry['flow']}"
            if entry.get("message"):
                text += f"  — {entry['message'][:50]}"
            item = QListWidgetItem(text)
            item.setForeground(QColor(color))
            item.setFont(QFont("Consolas", 10))
            self.history_list.addItem(item)

    def _copy_url(self):
        QApplication.clipboard().setText(self.server.url)

    def _open_dashboard(self):
        webbrowser.open(f"{self.server.url}/dashboard")

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            #api_header { background-color: #181825; }
            #api_title  { font-size: 15px; font-weight: 700; color: #89b4fa; }
            #api_status_on  { font-size: 12px; color: #a6e3a1; font-weight: 600; }
            #api_status_off { font-size: 12px; color: #f38ba8; font-weight: 600; }
            #api_sep    { color: #313244; }
            #api_footer { background-color: #181825; }
            #api_current { font-size: 11px; color: #6c7086; }
            #api_url {
                font-size: 14px; font-weight: 700; color: #cba6f7;
                font-family: monospace; padding: 4px 0;
            }

            QTabWidget::pane { border: none; background-color: #1e1e2e; }
            QTabBar::tab {
                background-color: #1e1e2e; color: #6c7086;
                padding: 8px 16px; font-size: 12px;
                border: none; border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #89b4fa; border-bottom: 2px solid #89b4fa; }
            QTabBar::tab:hover { color: #cdd6f4; }

            #endpoint_row {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 6px;
            }
            #endpoint_method { font-size: 11px; font-weight: 800; font-family: monospace; }
            #endpoint_path   { font-size: 12px; color: #cdd6f4; font-family: monospace; }
            #endpoint_desc   { font-size: 11px; color: #6c7086; }
            #endpoint_copy   { color: #45475a; font-size: 14px; }
            #endpoint_copy:hover { color: #cba6f7; }

            #example_title { font-size: 11px; font-weight: 700; color: #89b4fa; }
            #example_code {
                background-color: #11111b; border: 1px solid #313244;
                border-left: 3px solid #89b4fa; border-radius: 4px;
                padding: 8px 10px; color: #cdd6f4;
                font-size: 11px; font-family: monospace;
            }

            #api_history_list {
                background-color: #11111b; border: none;
                font-family: monospace; font-size: 11px;
            }
            #api_history_list::item { padding: 3px 8px; }
            #api_history_list::item:selected { background-color: #313244; }

            #btn_api_copy {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 5px 12px; font-size: 12px;
            }
            #btn_api_copy:hover { background-color: #45475a; }
            #btn_api_close {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 6px 16px; font-size: 12px;
            }
            #btn_api_close:hover { background-color: #45475a; }
            #btn_api_dashboard {
                background-color: #1c3a5c; color: #89b4fa;
                border: 1px solid #89b4fa; border-radius: 6px;
                padding: 5px 14px; font-size: 12px; font-weight: 600;
            }
            #btn_api_dashboard:hover { background-color: #1e3d66; }
        """)
