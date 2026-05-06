from blocks.base_block import BaseBlock


class IfBlock(BaseBlock):
    name = "Condição (Se)"
    description = (
        "Verifica uma condição. Se verdadeira, executa os blocos até 'Senão' ou 'Fim do Se'. "
        "Se falsa, pula para os blocos do 'Senão' (opcional) ou vai direto ao 'Fim do Se'. "
        "Sempre termine com um bloco 'Fim do Se'."
    )
    category = "Controle"

    params_schema = [
        {
            "name": "condition_type",
            "label": "Tipo de condição",
            "type": "str",
            "required": True,
            "default": "variable_equals",
            "placeholder": (
                "element_exists | element_not_exists | "
                "variable_equals | variable_not_equals | "
                "variable_contains | variable_not_contains | "
                "variable_greater | variable_less | variable_empty | variable_not_empty"
            ),
        },
        {
            "name": "selector",
            "label": "Seletor CSS (condições de elemento)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: .mensagem-erro  (só para element_exists / element_not_exists)",
        },
        {
            "name": "variable_name",
            "label": "Nome da variável (condições de variável)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: preco_extraido, url_atual",
        },
        {
            "name": "expected_value",
            "label": "Valor esperado (para equals / contains / greater / less)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Texto ou número a comparar",
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        ctype    = params.get("condition_type", "variable_equals").strip()
        selector = params.get("selector", "").strip()
        var_name = params.get("variable_name", "").strip()
        expected = params.get("expected_value", "").strip()

        result = False
        label  = ""

        try:
            # ── condições de elemento ──────────────────────────────────
            if ctype in ("element_exists", "element_not_exists"):
                from blocks.browser.open_browser import OpenBrowserBlock
                from selenium.webdriver.common.by import By
                driver = OpenBrowserBlock.get_driver()
                if not driver:
                    return {"success": False, "message": "Nenhum navegador aberto."}
                found = len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0
                result = found if ctype == "element_exists" else not found
                label  = f"Elemento '{selector}' {'existe' if found else 'não existe'}"

            # ── condições de variável ──────────────────────────────────
            elif ctype in (
                "variable_equals", "variable_not_equals",
                "variable_contains", "variable_not_contains",
                "variable_greater", "variable_less",
                "variable_empty", "variable_not_empty",
            ):
                from blocks.browser.extract_text import ExtractTextBlock
                raw = ExtractTextBlock._context.get(var_name, "")
                val = str(raw)

                if ctype == "variable_equals":
                    result = val.strip().lower() == expected.strip().lower()
                    label  = f"'{var_name}' == '{expected}'"
                elif ctype == "variable_not_equals":
                    result = val.strip().lower() != expected.strip().lower()
                    label  = f"'{var_name}' != '{expected}'"
                elif ctype == "variable_contains":
                    result = expected.lower() in val.lower()
                    label  = f"'{var_name}' contém '{expected}'"
                elif ctype == "variable_not_contains":
                    result = expected.lower() not in val.lower()
                    label  = f"'{var_name}' não contém '{expected}'"
                elif ctype == "variable_greater":
                    result = float(val) > float(expected)
                    label  = f"'{var_name}' ({val}) > {expected}"
                elif ctype == "variable_less":
                    result = float(val) < float(expected)
                    label  = f"'{var_name}' ({val}) < {expected}"
                elif ctype == "variable_empty":
                    result = val.strip() == ""
                    label  = f"'{var_name}' está vazio"
                elif ctype == "variable_not_empty":
                    result = val.strip() != ""
                    label  = f"'{var_name}' não está vazio"
            else:
                return {"success": False, "message": f"Tipo de condição desconhecido: '{ctype}'"}

            icon = "✓" if result else "✗"
            return {
                "success": True,
                "message": f"{icon} Se: {label} → {'VERDADEIRO' if result else 'FALSO'}",
                "data": {
                    "if_result": result,
                }
            }

        except (ValueError, TypeError) as e:
            return {"success": False, "message": f"Erro de comparação numérica: {e}"}
        except Exception as e:
            return {"success": False, "message": f"Erro na condição: {e}"}
