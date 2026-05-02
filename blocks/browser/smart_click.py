from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SmartClickBlock(BaseBlock):
    name        = "Smart Click"
    description = "Tenta clicar em um elemento usando até 3 seletores diferentes (redundância)."
    category    = "Navegador"

    params_schema = [
        {"name": "selector_1", "label": "Seletor Principal (XPath/CSS)", "type": "str", "required": True},
        {"name": "selector_2", "label": "Seletor de Backup 1", "type": "str", "required": False},
        {"name": "selector_3", "label": "Seletor de Backup 2", "type": "str", "required": False},
        {"name": "timeout_per_try", "label": "Timeout por tentativa (seg)", "type": "str", "default": "3"},
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Navegador não está aberto."}

        selectors = [
            params.get("selector_1"),
            params.get("selector_2"),
            params.get("selector_3")
        ]
        
        # Filtra seletores vazios
        selectors = [s for s in selectors if s and s.strip()]
        timeout = int(params.get("timeout_per_try", 3))

        for selector in selectors:
            try:
                # Detecta se é XPath ou CSS
                by_strategy = By.XPATH if selector.startswith("/") or selector.startswith("(") else By.CSS_SELECTOR
                
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by_strategy, selector))
                )
                element.click()
                return {"success": True, "message": f"Clicado com sucesso usando: {selector}"}
            except TimeoutException:
                continue # Tenta o próximo seletor
            except Exception as e:
                return {"success": False, "message": f"Erro inesperado: {str(e)}"}

        return {"success": False, "message": "Falha ao encontrar o elemento com todos os seletores fornecidos."}