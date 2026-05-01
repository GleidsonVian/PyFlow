import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QFrame, QWidget, QInputDialog, QMessageBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor


class FlowItem(QListWidgetItem):
    def __init__(self, name: str, filepath: str, modified: str):
        super().__init__()
        self.flow_name = name
        self.filepath  = filepath
        self.modified  = modified
        self.setSizeHint(QSize(0, 64))
        self.setFlags(self.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)


class FlowItemWidget(QWidget):
    def __init__(self, name: str, modified: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        lbl_name = QLabel(f"📄  {name}")
        lbl_name.setObjectName("flow_name")

        lbl_date = QLabel(modified)
        lbl_date.setObjectName("flow_date")

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_date)


class FlowManagerDialog(QDialog):
    flow_loaded = Signal(str)  # emite o filepath escolhido

    def __init__(self, flow_manager, parent=None):
        super().__init__(parent)
        self.flow_manager = flow_manager
        self.setWindowTitle("Gerenciador de Fluxos")
        self.setMinimumSize(520, 440)
        self.setModal(True)
        self._build_ui()
        self._apply_styles()
        self._load_flows()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("fm_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 16, 20, 16)

        title = QLabel("📁  Meus Fluxos")
        title.setObjectName("fm_title")

        self.lbl_count = QLabel("")
        self.lbl_count.setObjectName("fm_count")

        h.addWidget(title)
        h.addStretch()
        h.addWidget(self.lbl_count)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("fm_sep")
        root.addWidget(sep)

        # ── Lista ─────────────────────────────────────────────────
        self.list = QListWidget()
        self.list.setObjectName("fm_list")
        self.list.setSpacing(2)
        self.list.currentItemChanged.connect(self._on_selection)
        self.list.itemDoubleClicked.connect(self._on_load)
        root.addWidget(self.list, 1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("fm_sep")
        root.addWidget(sep2)

        # ── Barra de ações ────────────────────────────────────────
        actions = QWidget()
        actions.setObjectName("fm_actions")
        a = QHBoxLayout(actions)
        a.setContentsMargins(16, 12, 16, 12)
        a.setSpacing(8)

        self.btn_load = QPushButton("▶  Carregar")
        self.btn_load.setObjectName("btn_load")
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self._on_load)

        self.btn_rename = QPushButton("✏  Renomear")
        self.btn_rename.setObjectName("btn_action")
        self.btn_rename.setEnabled(False)
        self.btn_rename.clicked.connect(self._on_rename)

        self.btn_delete = QPushButton("🗑  Deletar")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_close")
        btn_close.clicked.connect(self.reject)

        a.addWidget(self.btn_load)
        a.addWidget(self.btn_rename)
        a.addWidget(self.btn_delete)
        a.addStretch()
        a.addWidget(btn_close)
        root.addWidget(actions)

    def _load_flows(self):
        self.list.clear()
        flows = self.flow_manager.list_flows()

        self.lbl_count.setText(f"{len(flows)} fluxo(s)")

        if not flows:
            empty = QListWidgetItem("Nenhum fluxo salvo ainda.")
            empty.setFlags(Qt.NoItemFlags)
            empty.setForeground(QColor("#45475a"))
            self.list.addItem(empty)
            return

        # Ordena por data de modificação (mais recente primeiro)
        flows.sort(key=lambda f: os.path.getmtime(f), reverse=True)

        for filepath in flows:
            name = os.path.basename(filepath).replace(".json", "").replace("_", " ").title()
            mtime = os.path.getmtime(filepath)
            from datetime import datetime
            modified = datetime.fromtimestamp(mtime).strftime("Modificado em %d/%m/%Y às %H:%M")

            item = FlowItem(name, filepath, modified)
            self.list.addItem(item)

            widget = FlowItemWidget(name, modified)
            self.list.setItemWidget(item, widget)

    def _on_selection(self, current, previous):
        has = current is not None and isinstance(current, FlowItem)
        self.btn_load.setEnabled(has)
        self.btn_rename.setEnabled(has)
        self.btn_delete.setEnabled(has)

    def _on_load(self):
        item = self.list.currentItem()
        if not isinstance(item, FlowItem):
            return
        self.flow_loaded.emit(item.filepath)
        self.accept()

    def _on_rename(self):
        item = self.list.currentItem()
        if not isinstance(item, FlowItem):
            return

        new_name, ok = QInputDialog.getText(
            self, "Renomear fluxo", "Novo nome:", text=item.flow_name
        )
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        old_path = item.filepath
        new_filename = new_name.replace(" ", "_").lower() + ".json"
        new_path = os.path.join(os.path.dirname(old_path), new_filename)

        try:
            # Atualiza o JSON com o novo nome
            import json
            with open(old_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["flow_name"] = new_name
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            if old_path != new_path:
                os.remove(old_path)

            self._load_flows()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível renomear:\n{str(e)}")

    def _on_delete(self):
        item = self.list.currentItem()
        if not isinstance(item, FlowItem):
            return

        reply = QMessageBox.question(
            self, "Deletar fluxo",
            f"Tem certeza que deseja deletar '{item.flow_name}'?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.flow_manager.delete(item.filepath)
            self._load_flows()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }

            #fm_header { background-color: #181825; }
            #fm_title {
                font-size: 16px; font-weight: 700; color: #cba6f7;
            }
            #fm_count { font-size: 12px; color: #6c7086; }
            #fm_sep { color: #313244; }

            #fm_list {
                background-color: #1e1e2e;
                border: none;
                padding: 8px;
            }
            #fm_list::item {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin: 2px 4px;
            }
            #fm_list::item:selected {
                background-color: #2a2a3e;
                border: 1.5px solid #cba6f7;
            }
            #fm_list::item:hover {
                background-color: #383850;
                border-color: #585b70;
            }

            .flow_name {
                font-size: 13px; font-weight: 600; color: #cdd6f4;
            }
            .flow_date {
                font-size: 11px; color: #6c7086;
            }
            #flow_name { font-size: 13px; font-weight: 600; color: #cdd6f4; }
            #flow_date { font-size: 11px; color: #6c7086; }

            #fm_actions { background-color: #181825; }

            #btn_load {
                background-color: #a6e3a1; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 7px 16px; font-weight: 600; font-size: 13px;
            }
            #btn_load:hover { background-color: #b9f0b3; }
            #btn_load:disabled { background-color: #45475a; color: #6c7086; }

            #btn_action {
                background-color: #313244; color: #cdd6f4;
                border: none; border-radius: 6px;
                padding: 7px 16px; font-size: 13px;
            }
            #btn_action:hover { background-color: #45475a; }
            #btn_action:disabled { background-color: #313244; color: #45475a; }

            #btn_delete {
                background-color: #3a1c1c; color: #f38ba8;
                border: 1px solid #f38ba8; border-radius: 6px;
                padding: 7px 16px; font-size: 13px;
            }
            #btn_delete:hover { background-color: #4a2020; }
            #btn_delete:disabled { background-color: #313244; color: #45475a; border-color: #45475a; }

            #btn_close {
                background-color: #313244; color: #6c7086;
                border: none; border-radius: 6px;
                padding: 7px 16px; font-size: 13px;
            }
            #btn_close:hover { background-color: #45475a; color: #cdd6f4; }

            QInputDialog {
                background-color: #1e1e2e; color: #cdd6f4;
            }
            QLineEdit {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 6px 10px;
                color: #cdd6f4; font-size: 13px;
            }
            QLineEdit:focus { border-color: #cba6f7; }
        """)
