from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock
from blocks.browser.extract_text import ExtractTextBlock


class GetCurrentUrlBlock(BaseBlock):
    name = "Obter URL Atual"
    description = "Captura a URL atual do navegador e salva em uma variável"
    category = "Navegador"

    params_schema = [
        {
            "name": "variable_name",
            "label": "Salvar como variável",
            "type": "str",
            "required": False,
            "default": "url_atual",
            "placeholder": "Nome da variável para guardar a URL"
        }
    ]

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        var_name = params.get("variable_name", "url_atual").strip() or "url_atual"

        try:
            url = driver.current_url
            ExtractTextBlock._context[var_name] = url
            return {
                "success": True,
                "message": f"URL capturada → {var_name}: \"{url}\"",
                "data": {"variable": var_name, "value": url}
            }
        except Exception as e:
            return {"success": False, "message": f"Erro ao obter URL: {str(e)}"}
