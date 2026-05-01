from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class FillFieldBlock(BaseBlock):
    name = "Preencher Campo"
    description = "Localiza um campo de texto e digita o valor informado"
    category = "Navegador"

    params_schema = [
        {
            "name": "selector",
            "label": "Seletor CSS",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: input[name='email'], #campo-cpf"
        },
        {
            "name": "value",
            "label": "Valor a digitar",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Texto que será digitado no campo"
        },
        {
            "name": "clear_before",
            "label": "Limpar campo antes de digitar",
            "type": "bool",
            "required": False,
            "default": True
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
        value = params.get("value", "")
        clear_before = params.get("clear_before", True)
        try:
            timeout = int(params.get("timeout", 10))
        except ValueError:
            timeout = 10

        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if clear_before:
                element.clear()
            element.send_keys(value)
            return {
                "success": True,
                "message": f"Campo '{selector}' preenchido com: {value}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao preencher '{selector}': {str(e)}"
            }
