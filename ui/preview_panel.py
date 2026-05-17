from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os

class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("preview_panel")
        self._current_widget = None
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setObjectName("preview_scroll")
        self.preview_scroll.setFrameShape(QFrame.NoFrame)

        self.preview_content = QWidget()
        self.preview_content.setObjectName("preview_content")
        self.preview_content_layout = QVBoxLayout(self.preview_content)
        self.preview_content_layout.setContentsMargins(12, 12, 12, 12)
        self.preview_content_layout.setSpacing(10)
        self.preview_content_layout.setAlignment(Qt.AlignTop)

        self.preview_empty = QLabel("Selecione um bloco\npara ver o preview e testes.")
        self.preview_empty.setObjectName("preview_empty")
        self.preview_empty.setAlignment(Qt.AlignCenter)
        self.preview_content_layout.addWidget(self.preview_empty)

        self.preview_scroll.setWidget(self.preview_content)
        layout.addWidget(self.preview_scroll)

    def show_block(self, canvas_widget):
        self._current_widget = canvas_widget
        self._clear_layout(self.preview_content_layout)
        self._populate_preview(canvas_widget)

    def clear(self):
        self._current_widget = None
        self._clear_layout(self.preview_content_layout)

        self.preview_empty = QLabel("Selecione um bloco\npara ver o preview e testes.")
        self.preview_empty.setObjectName("preview_empty")
        self.preview_empty.setAlignment(Qt.AlignCenter)
        self.preview_content_layout.addWidget(self.preview_empty)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_preview(self, canvas_widget):
        """Aba Preview: valida seletor, mostra último valor extraído e screenshot."""
        block  = canvas_widget.block_instance
        params = canvas_widget.params
        block_type = type(block).__name__

        name_label = QLabel(f"👁  Preview: {block.name}")
        name_label.setObjectName("preview_block_title")
        self.preview_content_layout.addWidget(name_label)

        sep_init = QFrame()
        sep_init.setFrameShape(QFrame.HLine)
        sep_init.setObjectName("separator")
        self.preview_content_layout.addWidget(sep_init)

        # ── Seletor ───────────────────────────────────────────────────
        selector = params.get("selector", "").strip()
        if selector:
            sel_title = QLabel("Seletor CSS")
            sel_title.setObjectName("preview_section")
            self.preview_content_layout.addWidget(sel_title)

            sel_box = QLabel(selector)
            sel_box.setObjectName("preview_selector")
            sel_box.setWordWrap(True)
            sel_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.preview_content_layout.addWidget(sel_box)

            # Botão verificar
            self._preview_result = QLabel("")
            self._preview_result.setObjectName("preview_result")
            self._preview_result.setWordWrap(True)

            btn_check = QPushButton("Verificar elemento no navegador")
            btn_check.setObjectName("btn_preview_check")
            btn_check.clicked.connect(lambda: self._check_selector(selector))
            self.preview_content_layout.addWidget(btn_check)
            self.preview_content_layout.addWidget(self._preview_result)
            self.preview_content_layout.addWidget(self._sep())

        # ── Último valor extraído (ExtractTextBlock / ExtractListBlock) ──
        var_name = params.get("variable_name", "")
        if var_name:
            try:
                from engine.execution_context import get as ctx_get
                ctx = ctx_get()
                value = ctx.get(var_name)
                if value is not None:
                    val_title = QLabel(f"Valor atual de  {{{{{var_name}}}}}")
                    val_title.setObjectName("preview_section")
                    self.preview_content_layout.addWidget(val_title)

                    display = str(value)
                    if isinstance(value, list):
                        display = f"Lista com {len(value)} itens:\n" + "\n".join(
                            f"  [{i}] {str(v)[:60]}" for i, v in enumerate(value[:8])
                        )
                        if len(value) > 8:
                            display += f"\n  ... +{len(value)-8} mais"
                    elif len(display) > 200:
                        display = display[:200] + "..."

                    val_box = QLabel(display)
                    val_box.setObjectName("preview_value")
                    val_box.setWordWrap(True)
                    val_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    self.preview_content_layout.addWidget(val_box)
                    self.preview_content_layout.addWidget(self._sep())
            except Exception:
                pass

        # ── Screenshot (ScreenshotBlock) ─────────────────────────────
        if block_type == "ScreenshotBlock":
            filename = params.get("filename", "screenshot.png")
            if filename and os.path.exists(filename):
                img_title = QLabel("Última screenshot")
                img_title.setObjectName("preview_section")
                self.preview_content_layout.addWidget(img_title)

                img_label = QLabel()
                pix = QPixmap(filename)
                if not pix.isNull():
                    pix = pix.scaledToWidth(250, Qt.SmoothTransformation)
                    img_label.setPixmap(pix)
                    img_label.setObjectName("preview_image")
                    img_label.setAlignment(Qt.AlignCenter)
                    self.preview_content_layout.addWidget(img_label)

        # ── URL atual (NavigateToUrlBlock / GetCurrentUrlBlock) ───────
        if block_type in ("NavigateToUrlBlock", "GetCurrentUrlBlock", "OpenBrowserBlock"):
            try:
                from blocks.browser.open_browser import OpenBrowserBlock as _OB
                driver = _OB.get_driver()
                if driver:
                    url_title = QLabel("URL atual do navegador")
                    url_title.setObjectName("preview_section")
                    self.preview_content_layout.addWidget(url_title)
                    url_val = QLabel(driver.current_url)
                    url_val.setObjectName("preview_value")
                    url_val.setWordWrap(True)
                    url_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    self.preview_content_layout.addWidget(url_val)
            except Exception:
                pass

        self.preview_content_layout.addStretch()

    def _check_selector(self, selector: str):
        """Valida o seletor CSS contra o navegador ativo e exibe o resultado."""
        try:
            from blocks.browser.open_browser import OpenBrowserBlock as _OB
            from selenium.webdriver.common.by import By
            driver = _OB.get_driver()
            if not driver:
                self._preview_result.setText("⚠️ Nenhum navegador aberto.")
                self._preview_result.setStyleSheet("color: #fab387; font-size: 12px; padding: 4px;")
                return
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            count = len(elements)
            if count == 0:
                self._preview_result.setText("❌  Elemento NÃO encontrado na página atual.")
                self._preview_result.setStyleSheet(
                    "color: #f38ba8; font-size: 12px; background: #2a1515; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
            elif count == 1:
                tag = elements[0].tag_name
                text = (elements[0].text or "")[:50]
                self._preview_result.setText(
                    f"✅  1 elemento encontrado\n"
                    f"    Tag: <{tag}>\n"
                    f"    Texto: {text}"
                )
                self._preview_result.setStyleSheet(
                    "color: #a6e3a1; font-size: 12px; background: #152a1a; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
            else:
                self._preview_result.setText(
                    f"⚠️  {count} elementos encontrados\n"
                    f"    O seletor não é único — pode pegar o elemento errado."
                )
                self._preview_result.setStyleSheet(
                    "color: #fab387; font-size: 12px; background: #2a2010; "
                    "border-radius: 6px; padding: 6px 10px;"
                )
        except Exception as e:
            self._preview_result.setText(f"Erro: {str(e)[:80]}")
            self._preview_result.setStyleSheet("color: #f38ba8; font-size: 12px;")

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        return sep

    def _apply_styles(self):
        self.setStyleSheet("""
            #preview_panel, #preview_scroll, #props_content { background-color: #181825; border: none; }
            #preview_empty { color: #45475a; font-size: 12px; padding: 30px 10px; }
            #preview_block_title { font-size: 14px; font-weight: 700; color: #cba6f7; }
            #separator { color: #313244; }
            #preview_section { font-size: 12px; font-weight: 700; color: #89b4fa; margin-top: 4px; }
            #preview_selector {
                background-color: #1e1e2e; border: 1px solid #45475a; border-left: 3px solid #cba6f7;
                border-radius: 5px; padding: 7px 10px; color: #cba6f7;
                font-size: 11px; font-family: monospace;
            }
            #btn_preview_check {
                background-color: #1a2a40; color: #89b4fa; border: 1px solid #89b4fa;
                border-radius: 6px; padding: 6px 12px; font-size: 12px; margin-top: 6px;
            }
            #btn_preview_check:hover { background-color: #1e3a50; }
            #preview_value {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 5px; padding: 8px 10px; color: #a6e3a1;
                font-size: 11px; font-family: monospace;
            }
            #preview_image { padding: 6px 0; }
        """)
