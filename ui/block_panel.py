from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QLineEdit, QFrame, QHBoxLayout,
    QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, QMimeData, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDrag, QColor, QFont, QCursor

from blocks.browser.open_browser         import OpenBrowserBlock
from blocks.browser.click_element        import ClickElementBlock
from blocks.browser.fill_field           import FillFieldBlock
from blocks.browser.screenshot           import ScreenshotBlock
from blocks.browser.extract_text         import ExtractTextBlock
from blocks.browser.extract_list         import ExtractListBlock
from blocks.browser.press_key            import PressKeyBlock
from blocks.browser.scroll_page          import ScrollPageBlock
from blocks.browser.get_current_url      import GetCurrentUrlBlock
from blocks.browser.mouse_action         import MouseActionBlock
from blocks.browser.smart_wait           import SmartWaitBlock
from blocks.browser.nav_controls         import (
    NavigateToUrlBlock, GoBackBlock, GoForwardBlock,
    RefreshPageBlock, OpenNewTabBlock, CloseTabBlock,
    SwitchTabBlock, CloseBrowserBlock
)
from blocks.control.wait                 import WaitBlock
from blocks.control.if_block             import IfBlock
from blocks.control.loop_block           import LoopBlock
from blocks.control.for_each_block       import ForEachBlock
from blocks.control.show_message         import ShowMessageBlock
from blocks.control.desktop_notification import DesktopNotificationBlock
from blocks.control.text_manipulation    import TextManipulationBlock
from blocks.control.set_variable         import SetVariableBlock
from blocks.control.sequence_start_block import SequenceStartBlock
from blocks.control.sequence_end_block   import SequenceEndBlock
from blocks.files.read_csv               import ReadCsvBlock
from blocks.files.save_text              import SaveTextBlock
from blocks.files.save_csv               import SaveCsvBlock
from blocks.files.sqlite_block           import SQLiteBlock
from blocks.integration.http_request     import HttpRequestBlock
from blocks.integration.send_email       import SendEmailBlock
from blocks.system.keyboard_action       import KeyboardActionBlock
from blocks.system.clipboard_block       import ClipboardBlock
from blocks.control.subflow_block        import SubfluxoBlock
from blocks.browser.execute_script       import ExecuteScriptBlock

AVAILABLE_BLOCKS = [
    OpenBrowserBlock,
    ClickElementBlock,
    FillFieldBlock,
    ExtractTextBlock,
    ExtractListBlock,
    PressKeyBlock,
    ScrollPageBlock,
    GetCurrentUrlBlock,
    ScreenshotBlock,
    MouseActionBlock,
    SmartWaitBlock,
    ExecuteScriptBlock,
    NavigateToUrlBlock,
    GoBackBlock,
    GoForwardBlock,
    RefreshPageBlock,
    OpenNewTabBlock,
    CloseTabBlock,
    SwitchTabBlock,
    CloseBrowserBlock,
    WaitBlock,
    IfBlock,
    LoopBlock,
    ForEachBlock,
    SetVariableBlock,
    SequenceStartBlock,
    SequenceEndBlock,
    ShowMessageBlock,
    DesktopNotificationBlock,
    TextManipulationBlock,
    SubfluxoBlock,
    KeyboardActionBlock,
    ClipboardBlock,
    ReadCsvBlock,
    SaveTextBlock,
    SaveCsvBlock,
    SQLiteBlock,
    HttpRequestBlock,
    SendEmailBlock,
]

# Ícone e cor de destaque por categoria
CATEGORY_META = {
    "Navegador":   {"icon": "🌐", "color": "#89b4fa"},
    "Controle":    {"icon": "🔧", "color": "#cba6f7"},
    "Arquivos":    {"icon": "📁", "color": "#a6e3a1"},
    "Integração":  {"icon": "🔌", "color": "#fab387"},
    "Sistema":     {"icon": "💻", "color": "#f38ba8"},
}


# ── Item de bloco arrastável ──────────────────────────────────────────

class BlockListItem(QListWidgetItem):
    def __init__(self, block_class):
        super().__init__()
        self.block_class = block_class
        self.setText(block_class.name)
        self.setToolTip(block_class.description)
        self.setSizeHint(QSize(0, 44))


class BlockListWidget(QListWidget):
    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not isinstance(item, BlockListItem):
            return
        mime = QMimeData()
        mime.setText(item.block_class.__name__)
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


# ── Seção colapsável de categoria ─────────────────────────────────────

class CategorySection(QWidget):
    """
    Seção colapsável com cabeçalho clicável e lista de blocos.
    Clique no cabeçalho para expandir/recolher.
    """

    def __init__(self, category: str, blocks: list, parent=None):
        super().__init__(parent)
        self.category   = category
        self.blocks     = blocks
        self._expanded  = True
        self._items: list[BlockListItem] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        meta  = CATEGORY_META.get(self.category, {"icon": "•", "color": "#cdd6f4"})
        color = meta["color"]
        icon  = meta["icon"]
        count = len(self.blocks)

        # ── Cabeçalho clicável ────────────────────────────────────────
        self.header = QWidget()
        self.header.setObjectName("cat_header")
        self.header.setCursor(QCursor(Qt.PointingHandCursor))
        self.header.setFixedHeight(34)

        h = QHBoxLayout(self.header)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(6)

        self.arrow = QLabel("▼")
        self.arrow.setObjectName("cat_arrow")
        self.arrow.setFixedWidth(14)
        self.arrow.setStyleSheet(f"color: {color}; font-size: 9px;")

        lbl_icon = QLabel(icon)
        lbl_icon.setObjectName("cat_icon")
        lbl_icon.setFixedWidth(18)

        lbl_name = QLabel(self.category.upper())
        lbl_name.setObjectName("cat_name")
        lbl_name.setStyleSheet(f"color: {color};")

        lbl_count = QLabel(str(count))
        lbl_count.setObjectName("cat_count")
        lbl_count.setStyleSheet(f"color: {color}; background-color: rgba(0,0,0,0.3); border-radius: 8px; padding: 0 6px;")

        h.addWidget(self.arrow)
        h.addWidget(lbl_icon)
        h.addWidget(lbl_name, 1)
        h.addWidget(lbl_count)

        self.header.mousePressEvent = lambda e: self._toggle()
        self.header.setStyleSheet(f"""
            QWidget#cat_header {{
                background-color: #181825;
                border-left: 2px solid {color};
                border-bottom: 1px solid #313244;
            }}
            QWidget#cat_header:hover {{
                background-color: #1e1e2e;
            }}
        """)
        layout.addWidget(self.header)

        # ── Lista de blocos ───────────────────────────────────────────
        self.list = BlockListWidget()
        self.list.setObjectName("block_list")
        self.list.setDragEnabled(True)
        self.list.setSelectionMode(QListWidget.SingleSelection)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for block_cls in self.blocks:
            item = BlockListItem(block_cls)
            self.list.addItem(item)
            self._items.append(item)

        # Ajusta altura da lista ao número de itens
        self._update_list_height()
        layout.addWidget(self.list)

    def _update_list_height(self):
        item_h = 44
        self.list.setFixedHeight(len(self.blocks) * item_h + 4)

    def _toggle(self):
        self._expanded = not self._expanded
        self.arrow.setText("▼" if self._expanded else "▶")
        self.list.setVisible(self._expanded)

    def set_filter(self, text: str):
        """Filtra blocos pelo texto e mostra/oculta seção conforme resultado."""
        visible = 0
        for item in self._items:
            match = text in item.text().lower()
            item.setHidden(not match)
            if match:
                visible += 1

        # Recalcula altura da lista para os itens visíveis
        self.list.setFixedHeight(max(visible * 44 + 4, 4))
        self.setVisible(visible > 0 or not text)

        # Durante busca, expande automaticamente
        if text and visible > 0:
            self._expanded = True
            self.arrow.setText("▼")
            self.list.setVisible(True)

    def expand_all(self):
        self._expanded = True
        self.arrow.setText("▼")
        self.list.setVisible(True)

    def collapse_all(self):
        self._expanded = False
        self.arrow.setText("▶")
        self.list.setVisible(False)


# ── Painel principal ──────────────────────────────────────────────────

class BlockPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("block_panel")
        self.setFixedWidth(220)
        self._sections: list[CategorySection] = []
        self._build_ui()
        self._apply_styles()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("panel_header")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(12, 12, 12, 8)
        h_layout.setSpacing(8)

        # Título + botões expandir/recolher tudo
        title_row = QHBoxLayout()
        title = QLabel("Blocos")
        title.setObjectName("panel_title")

        self.btn_expand_all = QPushButton("⊞")
        self.btn_expand_all.setObjectName("btn_expand_all")
        self.btn_expand_all.setFixedSize(22, 22)
        self.btn_expand_all.setToolTip("Expandir todas as categorias")
        self.btn_expand_all.clicked.connect(self._expand_all)

        self.btn_collapse_all = QPushButton("⊟")
        self.btn_collapse_all.setObjectName("btn_collapse_all")
        self.btn_collapse_all.setFixedSize(22, 22)
        self.btn_collapse_all.setToolTip("Recolher todas as categorias")
        self.btn_collapse_all.clicked.connect(self._collapse_all)

        title_row.addWidget(title, 1)
        title_row.addWidget(self.btn_expand_all)
        title_row.addWidget(self.btn_collapse_all)

        # Busca
        self.search = QLineEdit()
        self.search.setObjectName("search_box")
        self.search.setPlaceholderText("🔍  Buscar bloco...")
        self.search.textChanged.connect(self._filter)

        h_layout.addLayout(title_row)
        h_layout.addWidget(self.search)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # ── Scroll com seções ─────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setObjectName("panel_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.sections_widget = QWidget()
        self.sections_widget.setObjectName("sections_widget")
        self.sections_layout = QVBoxLayout(self.sections_widget)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(0)
        self.sections_layout.addStretch(1)

        self.scroll.setWidget(self.sections_widget)
        layout.addWidget(self.scroll, 1)

        # Dica de arrastar
        hint = QLabel("Arraste um bloco\npara o canvas →")
        hint.setObjectName("drag_hint")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def _populate(self):
        # Agrupa blocos por categoria mantendo a ordem de AVAILABLE_BLOCKS
        categories: dict[str, list] = {}
        for block_cls in AVAILABLE_BLOCKS:
            categories.setdefault(block_cls.category, []).append(block_cls)

        # Remove o stretch antes de adicionar seções
        self.sections_layout.takeAt(self.sections_layout.count() - 1)

        for cat, blocks in categories.items():
            section = CategorySection(cat, blocks)
            self._sections.append(section)
            self.sections_layout.addWidget(section)

        self.sections_layout.addStretch(1)

    def _filter(self, text: str):
        text = text.strip().lower()
        for section in self._sections:
            section.set_filter(text)

    def _expand_all(self):
        self.search.clear()
        for section in self._sections:
            section.expand_all()

    def _collapse_all(self):
        self.search.clear()
        for section in self._sections:
            section.collapse_all()

    def _apply_styles(self):
        self.setStyleSheet("""
            #block_panel    { background-color: #181825; }
            #panel_header   { background-color: #181825; }
            #panel_title    { font-size: 14px; font-weight: 700; color: #cdd6f4; }
            #separator      { color: #313244; }
            #panel_scroll, #sections_widget { background-color: #181825; }

            #search_box {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 10px;
                color: #cdd6f4; font-size: 12px;
            }
            #search_box:focus { border-color: #cba6f7; }

            #btn_expand_all, #btn_collapse_all {
                background-color: #313244; color: #6c7086;
                border: none; border-radius: 4px;
                font-size: 14px; font-weight: 700;
            }
            #btn_expand_all:hover, #btn_collapse_all:hover {
                background-color: #45475a; color: #cdd6f4;
            }

            #cat_icon  { font-size: 13px; }
            #cat_name  { font-size: 10px; font-weight: 800; letter-spacing: 0.5px; }
            #cat_count {
                font-size: 10px; font-weight: 700;
                min-width: 20px; max-width: 28px;
            }
            #cat_arrow { font-size: 9px; font-weight: 700; }

            #block_list {
                background-color: #181825;
                border: none;
                padding: 2px 4px;
            }
            #block_list::item {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 7px;
                padding: 6px 10px;
                margin: 2px 2px;
                color: #cdd6f4;
                font-size: 12px;
            }
            #block_list::item:hover {
                background-color: #313244;
                border-color: #cba6f7;
            }
            #block_list::item:selected {
                background-color: #313244;
                border-color: #cba6f7;
            }

            #drag_hint { color: #45475a; font-size: 11px; padding: 10px; }

            QScrollBar:vertical {
                background: #181825; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #45475a; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)