"""
Command Palette do PyFlow RPA.
Centro operacional centralizado para ações, busca de blocos e navegação.
Abre com Ctrl+P.
"""
from dataclasses import dataclass
from typing import Callable, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QHBoxLayout, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QKeyEvent, QColor, QFont

from engine.blocks_registry import ALL_BLOCKS

@dataclass
class Command:
    title: str
    category: str
    callback: Callable
    icon: str = "⚡"
    shortcut: str = ""
    data: Any = None  # Dados extras (ex: classe do bloco)

CATEGORY_ICONS = {
    "Ações":      "▶",
    "Projeto":    "📂",
    "Navegação":  "🔍",
    "Navegador":  "🌐",
    "Controle":   "🔧",
    "Arquivos":   "📁",
    "Integração": "🔌",
    "Sistema":    "💻",
    "Gatilhos":   "⚡",
    "Visão Computacional": "👁",
}

CATEGORY_COLORS = {
    "Ações":      "#a6e3a1",
    "Projeto":    "#89b4fa",
    "Navegação":  "#f9e2af",
    "Navegador":  "#89b4fa",
    "Controle":   "#cba6f7",
    "Arquivos":   "#a6e3a1",
    "Integração": "#fab387",
    "Sistema":    "#f38ba8",
    "Visão Computacional": "#cba6f7",
}


class PaletteItem(QListWidgetItem):
    def __init__(self, cmd: Command):
        super().__init__()
        self.cmd = cmd
        self.setSizeHint(QSize(0, 48))

    def set_custom_widget(self, list_widget: QListWidget):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        icon_lbl = QLabel(CATEGORY_ICONS.get(self.cmd.category, self.cmd.icon))
        icon_lbl.setFixedWidth(20)
        icon_lbl.setStyleSheet(f"color: {CATEGORY_COLORS.get(self.cmd.category, '#cdd6f4')}; font-size: 16px;")
        
        title_lbl = QLabel(self.cmd.title)
        title_lbl.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: 500;")
        
        shortcut_lbl = QLabel(self.cmd.shortcut)
        shortcut_lbl.setStyleSheet("color: #45475a; font-size: 11px; font-family: monospace;")
        shortcut_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl, 1)
        layout.addWidget(shortcut_lbl)
        
        list_widget.setItemWidget(self, widget)


class CommandPalette(QDialog):
    """
    Overlay central para busca global de comandos e blocos.
    """
    sig_add_block = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._global_commands: list[Command] = []
        
        self.setWindowTitle("")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(640)
        
        self._build_ui()
        self._apply_styles()

    def register_commands(self, commands: list[Command]):
        """Registra ações globais (ex: Salvar, Executar) vindas da MainWindow."""
        self._global_commands = commands
        self._populate("")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setObjectName("palette_container")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # ── Campo de busca ────────────────────────────────────────────
        search_row = QWidget()
        search_row.setObjectName("palette_search_row")
        s_layout = QHBoxLayout(search_row)
        s_layout.setContentsMargins(18, 14, 18, 14)
        s_layout.setSpacing(12)

        lbl_icon = QLabel("🔍")
        lbl_icon.setStyleSheet("font-size: 18px; color: #cba6f7;")

        self.search = QLineEdit()
        self.search.setObjectName("palette_search")
        self.search.setPlaceholderText("O que você deseja fazer? (Ações ou Blocos)")
        self.search.textChanged.connect(self._on_search)
        self.search.installEventFilter(self)

        s_layout.addWidget(lbl_icon)
        s_layout.addWidget(self.search, 1)
        c_layout.addWidget(search_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #313244;")
        c_layout.addWidget(sep)

        # ── Lista de resultados ───────────────────────────────────────
        self.list = QListWidget()
        self.list.setObjectName("palette_list")
        self.list.setMaximumHeight(400)
        self.list.itemActivated.connect(self._on_select)
        self.list.itemClicked.connect(self._on_select)
        c_layout.addWidget(self.list)

        # ── Footer ───────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("palette_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(18, 8, 18, 8)
        
        lbl_hint = QLabel("↑↓ para navegar  •  ENTER para executar  •  ESC para fechar")
        lbl_hint.setStyleSheet("font-size: 10px; color: #45475a;")
        f.addWidget(lbl_hint)
        f.addStretch()
        
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size: 10px; color: #45475a;")
        f.addWidget(self.lbl_count)

        c_layout.addWidget(footer)
        root.addWidget(container)

    def _populate(self, query: str):
        self.list.clear()
        q = query.lower().strip()

        # 1. Filtra Comandos Globais
        matches: list[Command] = []
        for cmd in self._global_commands:
            if not q or q in cmd.title.lower() or q in cmd.category.lower():
                matches.append(cmd)

        # 2. Filtra Blocos
        for cls in ALL_BLOCKS:
            if q and (q in cls.name.lower() or q in cls.category.lower()):
                matches.append(Command(
                    title=f"Adicionar: {cls.name}",
                    category=cls.category,
                    callback=None, # será tratado no _on_select
                    icon="➕",
                    data=cls
                ))

        # Agrupa por categoria para exibição
        grouped: dict[str, list[Command]] = {}
        for m in matches:
            grouped.setdefault(m.category, []).append(m)

        total = 0
        for cat in sorted(grouped.keys()):
            # Label de categoria
            cat_item = QListWidgetItem(f"   {cat.upper()}")
            cat_item.setFlags(Qt.NoItemFlags)
            cat_item.setForeground(QColor("#45475a"))
            cat_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            cat_item.setSizeHint(QSize(0, 24))
            self.list.addItem(cat_item)

            for cmd in grouped[cat]:
                item = PaletteItem(cmd)
                self.list.addItem(item)
                item.set_custom_widget(self.list)
                total += 1

        self.lbl_count.setText(f"{total} resultado(s)")
        
        # Seleciona o primeiro comando
        for i in range(self.list.count()):
            item = self.list.item(i)
            if isinstance(item, PaletteItem):
                self.list.setCurrentRow(i)
                break

    def _on_search(self, text: str):
        self._populate(text)

    def _on_select(self, item):
        if not isinstance(item, PaletteItem):
            return
        
        cmd = item.cmd
        self.close()
        
        if cmd.callback:
            cmd.callback()
        elif cmd.data: # É um bloco
            self.sig_add_block.emit(cmd.data)

    def eventFilter(self, obj, event):
        if obj is self.search and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._on_select(self.list.currentItem())
                return True
            elif event.key() == Qt.Key_Down:
                self._move_selection(1); return True
            elif event.key() == Qt.Key_Up:
                self._move_selection(-1); return True
            elif event.key() == Qt.Key_Escape:
                self.close(); return True
        return super().eventFilter(obj, event)

    def _move_selection(self, direction: int):
        row = self.list.currentRow()
        while 0 <= (row + direction) < self.list.count():
            row += direction
            if isinstance(self.list.item(row), PaletteItem):
                self.list.setCurrentRow(row)
                break

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            p = self.parent().geometry()
            self.move(p.x() + (p.width() - self.width()) // 2, p.y() + 80)
        self.search.clear()
        self.search.setFocus()

    def _apply_styles(self):
        self.setStyleSheet("""
            #palette_container {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 12px;
            }
            #palette_search_row { border-radius: 12px 12px 0 0; }
            #palette_search {
                background: transparent; border: none; color: #cdd6f4;
                font-size: 16px; font-family: 'Segoe UI';
            }
            #palette_list { background: transparent; border: none; outline: none; }
            #palette_list::item:selected { background-color: #313244; border-radius: 6px; }
            #palette_footer { background-color: #181825; border-radius: 0 0 12px 12px; }
        """)
