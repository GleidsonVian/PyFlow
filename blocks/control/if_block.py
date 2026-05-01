from selenium.webdriver.common.by import By

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock
from blocks.browser.extract_text import ExtractTextBlock


class IfBlock(BaseBlock):
    name = "Condição (If)"
    description = "Verifica uma condição. Se verdadeira, continua. Se falsa, pula os próximos N blocos."
    category = "Controle"

    params_schema = [
        {
            "name": "condition_type",
            "label": "Tipo de condição",
            "type": "str",
            "required": True,
            "default": "element_exists",
            "placeholder": "element_exists, element_not_exists, variable_contains, variable_equals"
        },
        {
            "name": "selector",
            "label": "Seletor CSS (para condições de elemento)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: .mensagem-erro, #btn-continuar"
        },
        {
            "name": "variable_name",
            "label": "Nome da variável (para condições de variável)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: texto_extraido, url_atual"
        },
        {
            "name": "expected_value",
            "label": "Valor esperado (para contains/equals)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Texto que a variável deve conter ou ser igual"
        },
        {
            "name": "skip_on_false",
            "label": "Blocos para pular se falso",
            "type": "str",
            "required": False,
            "default": "1",
            "placeholder": "Quantos blocos seguintes pular se condição for falsa"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        condition_type = params.get("condition_type", "element_exists").strip()
        selector       = params.get("selector", "").strip()
        variable_name  = params.get("variable_name", "").strip()
        expected_value = params.get("expected_value", "").strip()
        try:
            skip_on_false = int(params.get("skip_on_false", 1))
        except ValueError:
            skip_on_false = 1

        result = False

        try:
            if condition_type == "element_exists":
                driver = OpenBrowserBlock.get_driver()
                if not driver:
                    return {"success": False, "message": "Nenhum navegador aberto."}
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                result = len(elements) > 0
                label = f"Elemento '{selector}' {'existe' if result else 'não existe'}"

            elif condition_type == "element_not_exists":
                driver = OpenBrowserBlock.get_driver()
                if not driver:
                    return {"success": False, "message": "Nenhum navegador aberto."}
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                result = len(elements) == 0
                label = f"Elemento '{selector}' {'não existe (condição OK)' if result else 'existe (condição falhou)'}"

            elif condition_type == "variable_contains":
                context = ExtractTextBlock.get_context()
                value = str(context.get(variable_name, ""))
                result = expected_value.lower() in value.lower()
                label = f"Variável '{variable_name}' ({'contém' if result else 'não contém'}) '{expected_value}'"

            elif condition_type == "variable_equals":
                context = ExtractTextBlock.get_context()
                value = str(context.get(variable_name, ""))
                result = value.strip().lower() == expected_value.strip().lower()
                label = f"Variável '{variable_name}' ({'=' if result else '≠'}) '{expected_value}'"

            else:
                return {"success": False, "message": f"Tipo de condição desconhecido: '{condition_type}'"}

            return {
                "success": True,
                "message": f"{'✓' if result else '✗'} {label}",
                "data": {
                    "condition_result": result,
                    "skip_blocks": 0 if result else skip_on_false
                }
            }

        except Exception as e:
            return {"success": False, "message": f"Erro na condição: {str(e)}"}
