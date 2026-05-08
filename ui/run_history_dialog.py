from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import engine.run_history as history


class RunHistoryDialog(QDialog):
    flow_open_requested = Signal(str)
    resume_run_requested = Signal(str, int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de execuções")
        self.setMinimumSize(760, 440)
        self._build_ui()
        self._load()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        lbl = QLabel("📊  Histórico de execuções")
        lbl.setObjectName("hist_title")
        header.addWidget(lbl)
        header.addStretch()

        btn_clear = QPushButton("🗑  Limpar")
        btn_clear.setObjectName("btn_hist_clear")
        btn_clear.clicked.connect(self._on_clear)
        header.addWidget(btn_clear)
        root.addLayout(header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("hist_sep")
        root.addWidget(sep)

        self.table = QTableWidget()
        self.table.setObjectName("hist_table")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Fluxo", "Início", "Duração", "Passos", "OK", "Status", "Ação",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3, 4, 5, 6):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_hist_close")
        btn_close.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

    def _load(self):
        entries = history.get_history()
        self.table.setRowCount(len(entries))
        self._entries = entries
        for row, e in enumerate(entries):
            started = e.get("started_at", "")[:16].replace("T", " ")
            dur     = f"{e.get('duration_s', 0):.1f}s"
            total   = str(e.get("total_steps", 0))
            ok      = str(e.get("ok_steps", 0))
            success = e.get("success", False)
            status  = "✅ OK" if success else "❌ Falhou"
            color   = "#a6e3a1" if success else "#f38ba8"

            for col, text in enumerate([e.get("flow_name", ""), started, dur, total, ok, status]):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color if col == 5 else "#cdd6f4"))
                self.table.setItem(row, col, item)

            if e.get("flow_path"):
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(4)
                
                btn_open = QPushButton("📂 Abrir")
                btn_open.setObjectName("btn_hist_open")
                btn_open.clicked.connect(lambda _, path=e["flow_path"]: self._on_open(path))
                action_layout.addWidget(btn_open)
                
                if not success and e.get("failed_idx", -1) != -1:
                    btn_resume = QPushButton("▶ Retomar")
                    btn_resume.setObjectName("btn_hist_resume")
                    btn_resume.clicked.connect(lambda _, path=e["flow_path"], idx=e["failed_idx"], ctx=e.get("failed_context", {}): self._on_resume(path, idx, ctx))
                    action_layout.addWidget(btn_resume)
                    
                action_layout.addStretch()
                self.table.setCellWidget(row, 6, action_widget)

        self.table.setRowCount(len(entries))

    def _on_open(self, path: str):
        self.flow_open_requested.emit(path)
        self.accept()

    def _on_resume(self, path: str, failed_idx: int, ctx_snapshot: dict):
        self.resume_run_requested.emit(path, failed_idx, ctx_snapshot)
        self.accept()

    def _on_clear(self):
        if QMessageBox.question(self, "Limpar histórico", "Remover todo o histórico?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            history.clear_history()
            self.table.setRowCount(0)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; font-size: 13px; }
            #hist_title { font-size: 15px; font-weight: 600; color: #cba6f7; }
            #hist_sep { color: #313244; }
            #hist_table {
                background-color: #181825; border: 1px solid #313244;
                border-radius: 6px; gridline-color: #313244;
                alternate-background-color: #1e1e2e;
            }
            #hist_table::item { padding: 4px 8px; }
            #hist_table::item:selected { background-color: #313244; }
            QHeaderView::section {
                background-color: #181825; color: #6c7086;
                border: none; border-bottom: 1px solid #313244;
                padding: 6px 8px; font-size: 11px; font-weight: 600;
            }
            QPushButton { border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px; }
            #btn_hist_close { background-color: #313244; color: #cdd6f4; }
            #btn_hist_close:hover { background-color: #45475a; }
            #btn_hist_clear { background-color: #2e1a1a; color: #f38ba8; border: 1px solid #f38ba8; }
            #btn_hist_clear:hover { background-color: #3a1c1c; }
            #btn_hist_open { background-color: #1e2a40; color: #89b4fa; font-size: 11px; padding: 2px 8px; }
            #btn_hist_open:hover { background-color: #2a3a50; }
            #btn_hist_resume { background-color: #402a1e; color: #fab387; font-size: 11px; padding: 2px 8px; }
            #btn_hist_resume:hover { background-color: #503a2a; }
        """)
