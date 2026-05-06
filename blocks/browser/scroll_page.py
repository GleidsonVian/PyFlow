from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ScrollPageBlock(BaseBlock):
    name = "Scroll na Página"
    description = "Rola a página para cima, para baixo ou até um elemento específico"
    category = "Navegador"

    params_schema = [
        {
            "name":    "direction",
            "label":   "Direção",
            "type":    "select",
            "required": True,
            "default": "bottom",
            "options": [
                {"value": "bottom",  "label": "⬇ Ir para o final da página",  "description": "Rola até o rodapé — útil para páginas com carregamento infinito."},
                {"value": "top",     "label": "⬆ Ir para o início da página", "description": "Rola de volta ao topo da página."},
                {"value": "element", "label": "🎯 Rolar até um elemento",      "description": "Rola até que o elemento CSS especificado fique visível. Preencha o seletor abaixo."},
                {"value": "pixels",  "label": "📏 Rolar N pixels",             "description": "Rola exatamente a quantidade de pixels definida em 'Pixels'. Positivo = baixo, negativo = cima."},
            ],
        },
        {
            "name": "selector",
            "label": "Seletor CSS (só para direction=element)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: #rodape, .btn-carregar-mais"
        },
        {
            "name": "pixels",
            "label": "Pixels (só para direção personalizada)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: 500 (rola 500px para baixo)"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        direction = params.get("direction", "bottom").strip().lower()
        selector  = params.get("selector", "").strip()
        pixels    = params.get("pixels", "").strip()

        try:
            if direction == "top":
                driver.execute_script("window.scrollTo(0, 0);")
                return {"success": True, "message": "Scroll para o topo da página"}

            elif direction == "bottom":
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                return {"success": True, "message": "Scroll para o final da página"}

            elif direction == "element" and selector:
                from selenium.webdriver.common.by import By
                element = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                return {"success": True, "message": f"Scroll até o elemento: {selector}"}

            elif pixels:
                px = int(pixels)
                driver.execute_script(f"window.scrollBy(0, {px});")
                return {"success": True, "message": f"Scroll de {px}px"}

            else:
                return {"success": False, "message": "Parâmetros inválidos. Use direction: top, bottom ou element (com selector)."}

        except Exception as e:
            return {"success": False, "message": f"Erro ao fazer scroll: {str(e)}"}
