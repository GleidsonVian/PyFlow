import os
from datetime import datetime

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ScreenshotBlock(BaseBlock):
    name = "Tirar Screenshot"
    description = "Salva uma captura de tela da página atual do navegador"
    category = "Navegador"

    params_schema = [
        {
            "name": "filename",
            "label": "Nome do arquivo",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: captura_login (deixe vazio para usar data/hora)"
        },
        {
            "name": "folder",
            "label": "Pasta de destino",
            "type": "str",
            "required": False,
            "default": "screenshots",
            "placeholder": "screenshots"
        }
    ]

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto. Adicione o bloco 'Abrir Navegador' antes."}

        folder = params.get("folder", "screenshots").strip() or "screenshots"
        filename = params.get("filename", "").strip()

        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if not filename.endswith(".png"):
            filename += ".png"

        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)

        try:
            driver.save_screenshot(filepath)
            return {
                "success": True,
                "message": f"Screenshot salva em: {filepath}",
                "data": {"filepath": filepath}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao tirar screenshot: {str(e)}"
            }
