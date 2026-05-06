"""
Registro centralizado de blocos do PyFlow RPA.

Para adicionar um novo bloco:
  1. Importe a classe aqui
  2. Adicione-a à lista ALL_BLOCKS

Nada mais precisa ser alterado — BLOCK_BY_NAME é gerado automaticamente,
e block_panel.py / canvas.py importam daqui.
"""
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
from blocks.browser.smart_click          import SmartClickBlock
from blocks.browser.execute_script       import ExecuteScriptBlock
from blocks.browser.nav_controls         import (
    NavigateToUrlBlock, GoBackBlock, GoForwardBlock,
    RefreshPageBlock, OpenNewTabBlock, CloseTabBlock,
    SwitchTabBlock, CloseBrowserBlock,
)
from blocks.control.wait                 import WaitBlock
from blocks.control.if_block             import IfBlock
from blocks.control.else_block           import ElseBlock
from blocks.control.end_if_block         import EndIfBlock
from blocks.control.loop_block           import LoopBlock
from blocks.control.end_loop_block       import EndLoopBlock
from blocks.control.for_each_block       import ForEachBlock
from blocks.control.end_foreach_block    import EndForEachBlock
from blocks.control.while_block          import WhileBlock
from blocks.control.end_while_block      import EndWhileBlock
from blocks.control.try_block            import TryBlock
from blocks.control.catch_block          import CatchBlock
from blocks.control.end_try_block        import EndTryBlock
from blocks.control.set_variable         import SetVariableBlock
from blocks.control.sequence_start_block import SequenceStartBlock
from blocks.control.sequence_end_block   import SequenceEndBlock
from blocks.control.show_message         import ShowMessageBlock
from blocks.control.desktop_notification import DesktopNotificationBlock
from blocks.control.text_manipulation    import TextManipulationBlock
from blocks.control.subflow_block        import SubfluxoBlock
from blocks.files.read_csv               import ReadCsvBlock
from blocks.files.save_text              import SaveTextBlock
from blocks.files.save_csv               import SaveCsvBlock
from blocks.files.file_manager           import FileManagerBlock
from blocks.files.sqlite_block           import SQLiteBlock
from blocks.files.excel_block            import ExcelBlock
from blocks.files.load_env_block          import LoadEnvBlock
from blocks.files.zip_block              import ZipBlock
from blocks.integration.http_request     import HttpRequestBlock
from blocks.integration.send_email       import SendEmailBlock
from blocks.integration.send_webhook     import SendWebhookBlock
from blocks.integration.ftp_block        import FtpBlock
from blocks.system.keyboard_action       import KeyboardActionBlock
from blocks.system.clipboard_block       import ClipboardBlock
from blocks.system.hash_block            import HashBlock
from blocks.system.ocr_block             import OcrBlock
from blocks.system.python_script         import PythonScriptBlock
from blocks.trigger.timer_trigger        import TimerTriggerBlock
from blocks.trigger.webhook_trigger      import WebhookTriggerBlock

ALL_BLOCKS = [
    # Navegador
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
    SmartClickBlock,
    ExecuteScriptBlock,
    NavigateToUrlBlock,
    GoBackBlock,
    GoForwardBlock,
    RefreshPageBlock,
    OpenNewTabBlock,
    CloseTabBlock,
    SwitchTabBlock,
    CloseBrowserBlock,
    # Controle
    WaitBlock,
    IfBlock,
    ElseBlock,
    EndIfBlock,
    LoopBlock,
    EndLoopBlock,
    ForEachBlock,
    EndForEachBlock,
    WhileBlock,
    EndWhileBlock,
    TryBlock,
    CatchBlock,
    EndTryBlock,
    SetVariableBlock,
    SequenceStartBlock,
    SequenceEndBlock,
    ShowMessageBlock,
    DesktopNotificationBlock,
    TextManipulationBlock,
    SubfluxoBlock,
    # Arquivos
    LoadEnvBlock,
    ReadCsvBlock,
    SaveTextBlock,
    SaveCsvBlock,
    FileManagerBlock,
    SQLiteBlock,
    ExcelBlock,
    ZipBlock,
    # Integração
    HttpRequestBlock,
    SendEmailBlock,
    SendWebhookBlock,
    FtpBlock,
    # Sistema
    KeyboardActionBlock,
    ClipboardBlock,
    HashBlock,
    OcrBlock,
    PythonScriptBlock,
    # Gatilhos
    TimerTriggerBlock,
    WebhookTriggerBlock,
]

BLOCK_BY_NAME: dict[str, type] = {cls.__name__: cls for cls in ALL_BLOCKS}
