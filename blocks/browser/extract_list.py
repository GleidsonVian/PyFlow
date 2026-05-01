from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock
from blocks.browser.extract_text import ExtractTextBlock


class ExtractListBlock(BaseBlock):
    name = "Extrair Lista"
    description = "Extrai o texto de todos os elementos que correspondem a um seletor CSS e salva como lista no contexto. Use com o bloco 'Para Cada' para iterar."
    category = "Navegador"

    params_schema = [
        {
            "name": "selector",
            "label": "Seletor CSS",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: .product-title, h2.nome, ul li"
        },
        {
            "name": "attribute",
            "label": "Atributo a extrair (vazio = texto visível)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: href, src, data-id (vazio = texto)"
        },
        {
            "name": "variable_name",
            "label": "Salvar lista como variável",
            "type": "str",
            "required": False,
            "default": "lista_extraida",
            "placeholder": "Nome da variável que receberá a lista"
        },
        {
            "name": "limit",
            "label": "Limite de itens (0 = todos)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "0 = sem limite, 10 = primeiros 10"
        },
        {
            "name": "filter_empty",
            "label": "Ignorar itens vazios",
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
            return {"success": False, "message": "Nenhum navegador aberto."}

        selector     = params.get("selector", "").strip()
        attribute    = params.get("attribute", "").strip()
        var_name     = params.get("variable_name", "lista_extraida").strip() or "lista_extraida"
        filter_empty = params.get("filter_empty", True)
        try:
            limit   = int(params.get("limit", 0))
            timeout = int(params.get("timeout", 10))
        except ValueError:
            limit, timeout = 0, 10

        try:
            # Aguarda pelo menos 1 elemento aparecer
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            elements = driver.find_elements(By.CSS_SELECTOR, selector)

            # Extrai o valor de cada elemento
            values = []
            for el in elements:
                try:
                    if attribute:
                        val = el.get_attribute(attribute) or ""
                    else:
                        val = el.text.strip()
                        if not val:
                            val = driver.execute_script("return arguments[0].innerText;", el) or ""
                            val = val.strip()
                    values.append(val)
                except Exception:
                    values.append("")

            # Filtra vazios
            if filter_empty:
                values = [v for v in values if v]

            # Aplica limite
            if limit > 0:
                values = values[:limit]

            # Salva no contexto
            ExtractTextBlock._context[var_name] = values
            ExtractTextBlock._context[f"{var_name}_total"] = str(len(values))
            if values:
                ExtractTextBlock._context[f"{var_name}_primeiro"] = values[0]

            preview = ", ".join(f'"{v[:30]}"' for v in values[:3])
            if len(values) > 3:
                preview += f" ... (+{len(values) - 3})"

            return {
                "success": True,
                "message": f"Lista extraída: {len(values)} item(s) → '{var_name}': [{preview}]",
                "data": {
                    "variable": var_name,
                    "count": len(values),
                    "values": values
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao extrair lista de '{selector}': {str(e).split('Stacktrace')[0].strip()}"
            }
