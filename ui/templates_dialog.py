"""
Tela de seleção de templates do PyFlow RPA.
Coloque em: ui/templates_dialog.py
"""
import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget, QScrollArea,
    QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


TEMPLATES = [
    {
        "id":          "template_scraping_lista",
        "title":       "Scraping de Lista",
        "icon":        "🌐",
        "category":    "Web",
        "description": "Extrai títulos, preços e links de uma página de listagem e salva em CSV.",
        "steps":       10,
        "tags":        ["scraping", "csv", "lista", "web"],
    },
    {
        "id":          "template_monitor_preco",
        "title":       "Monitor de Preço",
        "icon":        "💰",
        "category":    "Web",
        "description": "Monitora o preço de um produto e envia e-mail se o valor mudar.",
        "steps":       9,
        "tags":        ["monitor", "preço", "email", "web"],
    },
    {
        "id":          "template_login_extracao",
        "title":       "Login + Extração",
        "icon":        "🔐",
        "category":    "Web",
        "description": "Faz login em um site e extrai dados autenticados, com screenshot.",
        "steps":       12,
        "tags":        ["login", "autenticação", "extração", "web"],
    },
    {
        "id":          "template_preencher_formulario",
        "title":       "Preencher Formulário",
        "icon":        "📝",
        "category":    "Automação",
        "description": "Lê dados de um CSV e submete cada linha em um formulário web em loop.",
        "steps":       12,
        "tags":        ["formulário", "csv", "loop", "web"],
    },
    {
        "id":          "template_disparo_api",
        "title":       "Disparo de API",
        "icon":        "🔌",
        "category":    "Integração",
        "description": "Lê um CSV e faz uma requisição HTTP para cada linha, salvando respostas.",
        "steps":       7,
        "tags":        ["api", "http", "csv", "integração"],
    },
]

CATEGORY_COLORS = {
    "Web":        "#89b4fa",
    "Automação":  "#cba6f7",
    "Integração": "#fab387",
}


class TemplateCard(QWidget):
    clicked = Signal(dict)

    def __init__(self, template: dict, parent=None):
        super().__init__(parent)
        self.template = template
        self.setObjectName("template_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(260, 160)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header: ícone + categoria
        header = QHBoxLayout()
        lbl_icon = QLabel(self.template["icon"])
        lbl_icon.setObjectName("card_icon")

        cat = self.template["category"]
        color = CATEGORY_COLORS.get(cat, "#cdd6f4")
        lbl_cat = QLabel(cat)
        lbl_cat.setObjectName("card_category")
        lbl_cat.setStyleSheet(f"color: {color}; background-color: transparent;")

        lbl_steps = QLabel(f"{self.template['steps']} passos")
        lbl_steps.setObjectName("card_steps")

        header.addWidget(lbl_icon)
        header.addWidget(lbl_cat)
        header.addStretch()
        header.addWidget(lbl_steps)
        layout.addLayout(header)

        # Título
        lbl_title = QLabel(self.template["title"])
        lbl_title.setObjectName("card_title")
        layout.addWidget(lbl_title)

        # Descrição
        lbl_desc = QLabel(self.template["description"])
        lbl_desc.setObjectName("card_desc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc, 1)

        # Tags
        tags_row = QHBoxLayout()
        tags_row.setSpacing(4)
        for tag in self.template["tags"][:3]:
            lbl_tag = QLabel(f"#{tag}")
            lbl_tag.setObjectName("card_tag")
            tags_row.addWidget(lbl_tag)
        tags_row.addStretch()
        layout.addLayout(tags_row)

    def _apply_styles(self):
        self.setStyleSheet("""
            #template_card {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 10px;
            }
            #template_card:hover {
                border-color: #cba6f7;
                background-color: #252535;
            }
            #card_icon   { font-size: 20px; }
            #card_category { font-size: 10px; font-weight: 700; margin-left: 6px; }
            #card_steps  { font-size: 10px; color: #45475a; }
            #card_title  { font-size: 13px; font-weight: 700; color: #cdd6f4; }
            #card_desc   { font-size: 11px; color: #6c7086; }
            #card_tag    {
                font-size: 10px; color: #45475a;
                background-color: #313244; border-radius: 4px;
                padding: 1px 6px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.template)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(
            "border-color: #cba6f7;", "border-color: #cba6f7 !important;"))
        super().enterEvent(event)


class TemplatesDialog(QDialog):
    template_selected = Signal(str)   # emite o filepath do JSON

    def __init__(self, templates_dir: str = "flows", parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self.setWindowTitle("📋  Templates de Fluxos")
        self.setMinimumSize(620, 520)
        self.setModal(True)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("tmpl_header")
        h = QVBoxLayout(header)
        h.setContentsMargins(20, 16, 20, 12)
        h.setSpacing(4)

        title = QLabel("📋  Templates de Fluxos")
        title.setObjectName("tmpl_title")

        subtitle = QLabel("Escolha um template para começar rapidamente. Os parâmetros podem ser editados após carregar.")
        subtitle.setObjectName("tmpl_subtitle")
        subtitle.setWordWrap(True)

        h.addWidget(title)
        h.addWidget(subtitle)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("tmpl_sep")
        root.addWidget(sep)

        # ── Grid de cards ─────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("tmpl_scroll")
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("tmpl_content")
        grid = QGridLayout(content)
        grid.setContentsMargins(20, 16, 20, 16)
        grid.setSpacing(14)

        col = 0
        row = 0
        for tmpl in TEMPLATES:
            card = TemplateCard(tmpl)
            card.clicked.connect(self._on_card_clicked)
            grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("tmpl_sep")
        root.addWidget(sep2)

        # ── Footer ────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("tmpl_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(20, 10, 20, 10)

        hint = QLabel("💡  Clique em um template para carregá-lo no canvas.")
        hint.setObjectName("tmpl_hint")

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_tmpl_close")
        btn_close.clicked.connect(self.reject)

        f.addWidget(hint, 1)
        f.addWidget(btn_close)
        root.addWidget(footer)

    def _on_card_clicked(self, template: dict):
        """Localiza o JSON do template e emite o path."""
        filename = f"{template['id']}.json"

        # Procura na pasta flows/
        path = os.path.join(self.templates_dir, filename)
        if not os.path.exists(path):
            # Tenta na pasta raiz
            path = filename
        if not os.path.exists(path):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Template não encontrado",
                f"Arquivo '{filename}' não encontrado na pasta flows/.\n\n"
                f"Copie os arquivos de template para a pasta flows/ do projeto.")
            return

        self.template_selected.emit(path)
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            #tmpl_header { background-color: #181825; }
            #tmpl_title  { font-size: 16px; font-weight: 700; color: #cba6f7; }
            #tmpl_subtitle { font-size: 12px; color: #6c7086; }
            #tmpl_sep    { color: #313244; }
            #tmpl_scroll, #tmpl_content { background-color: #1e1e2e; }
            #tmpl_footer { background-color: #181825; }
            #tmpl_hint   { font-size: 11px; color: #45475a; font-style: italic; }
            #btn_tmpl_close {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 6px 20px; font-size: 13px;
            }
            #btn_tmpl_close:hover { background-color: #45475a; }
            QScrollBar:vertical { background: #1e1e2e; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
