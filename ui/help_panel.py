from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel
from PySide6.QtCore import Qt
from ui.block_docs import BLOCK_DOCS

class HelpPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("help_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header (pode ser o nome do bloco)
        self.lbl_title = QLabel("Nenhum bloco selecionado")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #cba6f7;")
        layout.addWidget(self.lbl_title)
        
        # TextBrowser para documentação em Markdown/HTML
        self.browser = QTextBrowser()
        self.browser.setObjectName("help_browser")
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.browser)
        
        self.clear()

    def show_block(self, node_item):
        """Atualiza o painel com a documentação do bloco."""
        if not node_item:
            self.clear()
            return

        block_class_name = type(node_item.block_instance).__name__
        doc = BLOCK_DOCS.get(block_class_name)
        
        if not doc:
            self.lbl_title.setText(block_class_name)
            self.browser.setHtml(f"<p>Documentação não encontrada para <b>{block_class_name}</b>.</p>")
            return
            
        self.lbl_title.setText(doc.get("title", block_class_name))
        
        # Build HTML content
        html = f"""
        <style>
            h3 {{ color: #89b4fa; font-size: 13px; margin-top: 15px; margin-bottom: 5px; }}
            p {{ margin-top: 0; margin-bottom: 10px; color: #a6adc8; }}
            ul {{ margin-top: 0; padding-left: 20px; }}
            li {{ margin-bottom: 4px; color: #a6adc8; }}
            b {{ color: #cdd6f4; }}
            .tip {{ background-color: #313244; padding: 10px; border-radius: 6px; border-left: 4px solid #f9e2af; margin-top: 15px; color: #f9e2af; }}
            pre {{ background-color: #181825; padding: 10px; border-radius: 6px; color: #a6e3a1; font-family: Consolas, monospace; font-size: 12px; }}
        </style>
        """
        
        desc = doc.get("description", "")
        if desc:
            html += f"<p>{desc}</p>"
            
        params = doc.get("params", [])
        if params:
            html += "<h3>Parâmetros:</h3><ul>"
            for p_name, p_type, p_req, p_desc in params:
                req_text = " (Obrigatório)" if p_req.lower() == "sim" else ""
                html += f"<li><b>{p_name}</b> <i>[{p_type}]</i>{req_text}<br>{p_desc}</li>"
            html += "</ul>"
            
        example = doc.get("example", "")
        if example:
            html += f"<h3>Exemplo de Uso:</h3><pre>{example}</pre>"
            
        tip = doc.get("tip", "")
        if tip:
            html += f"<div class='tip'><b>💡 Dica:</b> {tip}</div>"
            
        self.browser.setHtml(html)

    def clear(self):
        """Limpa o painel e mostra atalhos gerais."""
        self.lbl_title.setText("PyFlow RPA - Ajuda")
        html = """
        <style>
            h3 { color: #89b4fa; font-size: 13px; margin-top: 15px; margin-bottom: 5px; }
            p { margin-top: 0; margin-bottom: 10px; color: #a6adc8; }
            ul { margin-top: 0; padding-left: 20px; }
            li { margin-bottom: 8px; color: #a6adc8; }
            b { color: #cba6f7; }
        </style>
        <p>Selecione um bloco no canvas para ver a documentação detalhada.</p>
        <h3>Atalhos Rápidos:</h3>
        <ul>
            <li><b>Ctrl + P</b>: Abrir Command Palette (buscar blocos)</li>
            <li><b>Ctrl + Enter</b>: Executar fluxo inteiro</li>
            <li><b>Ctrl + B</b>: Esconder/Mostrar painel direito</li>
            <li><b>Ctrl + D</b>: Iniciar depuração (Debug)</li>
            <li><b>Duplo Clique no Canvas</b>: Edição livre</li>
            <li><b>Botão Direito</b>: Adicionar Post-it</li>
        </ul>
        """
        self.browser.setHtml(html)
