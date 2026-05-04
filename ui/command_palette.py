"""
Command Palette do PyFlow RPA.
Abre com Ctrl+P — busca e adiciona blocos rapidamente sem usar o painel lateral.
Coloque em: ui/command_palette.py
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QHBoxLayout, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QKeyEvent, QColor

from engine.blocks_registry import ALL_BLOCKS

CATEGORY_ICONS = {
    "Navegador":  "🌐",
    "Controle":   "🔧",
    "Arquivos":   "📁",
    "Integração": "🔌",
    "Sistema":    "💻",
}

CATEGORY_COLORS = {
    "Navegador":  "#89b4fa",
    "Controle":   "#cba6f7",
    "Arquivos":   "#a6e3a1",
    "Integração": "#fab387",
    "Sistema":    "#f38ba8",
}


class PaletteItem(QListWidgetItem):
    def __init__(self, block_cls):
        super().__init__()
        self.block_cls = block_cls
        cat = block_cls.category
        icon = CATEGORY_ICONS.get(cat, "▪")
        self.setText(f"{icon}  {block_cls.name}")
        self.setToolTip(block_cls.description)
        self.setSizeHint(QSize(0, 52))
        color = CATEGORY_COLORS.get(cat, "#cdd6f4")
        self.setForeground(QColor(color))


class CommandPalette(QDialog):
    """
    Popup de busca global de blocos.
    Abre com Ctrl+P, fecha com Escape.
    Enter ou duplo clique adiciona o bloco ao canvas.
    """
    block_selected = Signal(object)   # emite a classe do bloco escolhido

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(520)
        self._build_ui()
        self._apply_styles()
        self._populate("")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Container com borda arredondada
        container = QWidget()
        container.setObjectName("palette_container")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # ── Campo de busca ────────────────────────────────────────────
        search_row = QWidget()
        search_row.setObjectName("palette_search_row")
        s_layout = QHBoxLayout(search_row)
        s_layout.setContentsMargins(14, 12, 14, 12)
        s_layout.setSpacing(10)

        lbl_icon = QLabel("⚡")
        lbl_icon.setObjectName("palette_icon")

        self.search = QLineEdit()
        self.search.setObjectName("palette_search")
        self.search.setPlaceholderText("Buscar bloco... (Ex: extrair, http, csv)")
        self.search.textChanged.connect(self._on_search)
        self.search.installEventFilter(self)

        lbl_esc = QLabel("ESC para fechar")
        lbl_esc.setObjectName("palette_esc_hint")

        s_layout.addWidget(lbl_icon)
        s_layout.addWidget(self.search, 1)
        s_layout.addWidget(lbl_esc)
        c_layout.addWidget(search_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("palette_sep")
        c_layout.addWidget(sep)

        # ── Lista de resultados ───────────────────────────────────────
        self.list = QListWidget()
        self.list.setObjectName("palette_list")
        self.list.setMaximumHeight(360)
        self.list.itemActivated.connect(self._on_select)
        self.list.itemDoubleClicked.connect(self._on_select)
        c_layout.addWidget(self.list)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("palette_sep")
        c_layout.addWidget(sep2)

        # ── Footer com dicas ──────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("palette_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(14, 8, 14, 8)
        f.setSpacing(16)

        hints = [
            ("↑↓", "navegar"),
            ("Enter", "adicionar bloco"),
            ("Ctrl+P", "abrir/fechar"),
        ]
        for key, desc in hints:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl_key = QLabel(key)
            lbl_key.setObjectName("palette_key")
            lbl_desc = QLabel(desc)
            lbl_desc.setObjectName("palette_hint_desc")
            row.addWidget(lbl_key)
            row.addWidget(lbl_desc)
            f.addLayout(row)

        f.addStretch()

        self.lbl_count = QLabel("")
        self.lbl_count.setObjectName("palette_count")
        f.addWidget(self.lbl_count)

        c_layout.addWidget(footer)
        root.addWidget(container)

    def _populate(self, query: str):
        self.list.clear()
        q = query.lower().strip()

        # Agrupa por categoria
        grouped: dict[str, list] = {}
        for cls in ALL_BLOCKS:
            if q == "" or q in cls.name.lower() or q in cls.category.lower() or q in cls.description.lower():
                grouped.setdefault(cls.category, []).append(cls)

        total = 0
        for cat, blocks in grouped.items():
            # Cabeçalho da categoria
            icon = CATEGORY_ICONS.get(cat, "▪")
            color = CATEGORY_COLORS.get(cat, "#cdd6f4")
            cat_item = QListWidgetItem(f"  {icon}  {cat.upper()}")
            cat_item.setFlags(Qt.NoItemFlags)
            cat_item.setForeground(QColor(color))
            cat_item.setSizeHint(QSize(0, 26))
            self.list.addItem(cat_item)

            for cls in blocks:
                item = PaletteItem(cls)
                self.list.addItem(item)
                total += 1

        self.lbl_count.setText(f"{total} bloco(s)")

        # Seleciona o primeiro item válido
        for i in range(self.list.count()):
            item = self.list.item(i)
            if isinstance(item, PaletteItem):
                self.list.setCurrentItem(item)
                break

    def _on_search(self, text: str):
        self._populate(text)

    def _on_select(self, item):
        if isinstance(item, PaletteItem):
            self.block_selected.emit(item.block_cls)
            self.close()

    def eventFilter(self, obj, event):
        """Intercepta teclas no campo de busca."""
        if obj is self.search and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                current = self.list.currentItem()
                if isinstance(current, PaletteItem):
                    self._on_select(current)
                return True

            elif event.key() == Qt.Key_Down:
                self._move_selection(1)
                return True

            elif event.key() == Qt.Key_Up:
                self._move_selection(-1)
                return True

            elif event.key() == Qt.Key_Escape:
                self.close()
                return True

        return super().eventFilter(obj, event)

    def _move_selection(self, direction: int):
        """Move a seleção ignorando itens de categoria (não selecionáveis)."""
        current = self.list.currentRow()
        count   = self.list.count()
        next_row = current + direction

        while 0 <= next_row < count:
            item = self.list.item(next_row)
            if isinstance(item, PaletteItem):
                self.list.setCurrentRow(next_row)
                self.list.scrollToItem(item)
                return
            next_row += direction

    def showEvent(self, event):
        """Centraliza o dialog na janela pai e foca no campo de busca."""
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + int(parent_geo.height() * 0.15)
            self.move(x, y)
        self.search.clear()
        self.search.setFocus()
        self._populate("")

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background: transparent; }

            #palette_container {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 12px;
            }

            #palette_search_row {
                background-color: #1e1e2e;
                border-radius: 12px 12px 0 0;
            }

            #palette_icon { font-size: 18px; color: #cba6f7; }

            #palette_search {
                background: transparent;
                border: none;
                color: #cdd6f4;
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
            #palette_search:focus { outline: none; }

            #palette_esc_hint {
                font-size: 11px; color: #45475a;
                background-color: #313244;
                border-radius: 4px; padding: 2px 6px;
            }

            #palette_sep { color: #313244; }

            #palette_list {
                background-color: #1e1e2e;
                border: none;
                font-size: 13px;
                outline: none;
            }
            #palette_list::item {
                padding: 10px 16px;
                border-radius: 0;
                color: #cdd6f4;
            }
            #palette_list::item:selected {
                background-color: #313244;
                color: #cba6f7;
            }
            #palette_list::item:hover {
                background-color: #252535;
            }

            #palette_footer {
                background-color: #181825;
                border-radius: 0 0 12px 12px;
            }

            #palette_key {
                background-color: #313244;
                color: #a6adc8;
                font-size: 11px;
                font-family: monospace;
                border-radius: 4px;
                padding: 1px 6px;
            }
            #palette_hint_desc { font-size: 11px; color: #45475a; }
            #palette_count { font-size: 11px; color: #45475a; }
        """)
