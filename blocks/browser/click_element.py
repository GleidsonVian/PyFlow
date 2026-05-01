from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ClickElementBlock(BaseBlock):
    name = "Clicar em Elemento"
    description = "Clica em um elemento da página usando seletor CSS ou XPath"
    category = "Navegador"

    params_schema = [
        {
            "name": "selector",
            "label": "Seletor CSS",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: button#submit, .btn-login, input[type='submit']"
        },
        {
            "name": "timeout",
            "label": "Tempo de espera (segundos)",
            "type": "str",
            "required": False,
            "default": "10",
            "placeholder": "10"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto. Adicione o bloco 'Abrir Navegador' antes."}

        selector = params.get("selector", "").strip()
        try:
            timeout = int(params.get("timeout", 10))
        except ValueError:
            timeout = 10

        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return {
                "success": True,
                "message": f"Elemento clicado: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao clicar em '{selector}': {str(e)}"
            }
