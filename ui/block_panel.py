from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, QMimeData, QSize
from PySide6.QtGui import QDrag, QColor, QFont

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
from blocks.integration.ftp_block        import FtpBlock
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
    KeyboardActionBlock,
    ClipboardBlock,
    ReadCsvBlock,
    SaveTextBlock,
    SaveCsvBlock,
    SQLiteBlock,
    HttpRequestBlock,
    SendEmailBlock,
    SubfluxoBlock,
    ExecuteScriptBlock,
    FtpBlock,
]


class BlockListItem(QListWidgetItem):
    def __init__(self, block_class):
        super().__init__()
        self.block_class = block_class
        self.setText(block_class.name)
        self.setToolTip(block_class.description)
        self.setSizeHint(QSize(0, 48))


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


class BlockPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("block_panel")
        self.setFixedWidth(220)
        self._build_ui()
        self._apply_styles()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("panel_header")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(12, 12, 12, 10)
        h_layout.setSpacing(8)

        title = QLabel("Blocos")
        title.setObjectName("panel_title")

        self.search = QLineEdit()
        self.search.setObjectName("search_box")
        self.search.setPlaceholderText("🔍  Buscar bloco...")
        self.search.textChanged.connect(self._filter)

        h_layout.addWidget(title)
        h_layout.addWidget(self.search)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        self.list = BlockListWidget()
        self.list.setObjectName("block_list")
        self.list.setDragEnabled(True)
        self.list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.list, 1)

        hint = QLabel("Arraste um bloco\npara o canvas →")
        hint.setObjectName("drag_hint")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def _populate(self):
        categories = {}
        for block_cls in AVAILABLE_BLOCKS:
            categories.setdefault(block_cls.category, []).append(block_cls)

        for cat, blocks in categories.items():
            cat_item = QListWidgetItem(f"  {cat.upper()}")
            cat_item.setFlags(Qt.NoItemFlags)
            cat_item.setForeground(QColor("#6c7086"))
            f = QFont()
            f.setPointSize(9)
            f.setBold(True)
            cat_item.setFont(f)
            cat_item.setSizeHint(QSize(0, 28))
            self.list.addItem(cat_item)
            for block_cls in blocks:
                self.list.addItem(BlockListItem(block_cls))

    def _filter(self, text):
        text = text.lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            if isinstance(item, BlockListItem):
                item.setHidden(text not in item.text().lower())
            else:
                item.setHidden(False)

    def _apply_styles(self):
        self.setStyleSheet("""
            #block_panel { background-color: #181825; }
            #panel_header { background-color: #181825; }
            #panel_title { font-size: 14px; font-weight: 600; color: #cdd6f4; padding: 0; }
            #search_box {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 10px; color: #cdd6f4; font-size: 12px;
            }
            #search_box:focus { border-color: #cba6f7; }
            #separator { color: #313244; }
            #block_list { background-color: #181825; border: none; padding: 4px; }
            #block_list::item {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 8px; padding: 8px 12px; margin: 2px 4px;
                color: #cdd6f4; font-size: 13px;
            }
            #block_list::item:hover { background-color: #313244; border-color: #cba6f7; }
            #block_list::item:selected { background-color: #313244; border-color: #cba6f7; }
            #drag_hint { color: #45475a; font-size: 11px; padding: 12px; }
        """)