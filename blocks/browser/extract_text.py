from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import engine.execution_context as _ctx
from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ExtractTextBlock(BaseBlock):
    name = "Extrair Texto"
    description = "Extrai o texto de um elemento da página e salva no contexto de execução"
    category = "Navegador"

    params_schema = [
        {
            "name": "selector",
            "label": "Seletor CSS",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: h1.titulo, #resultado, .preco"
        },
        {
            "name": "variable_name",
            "label": "Salvar como variável",
            "type": "str",
            "required": False,
            "default": "texto_extraido",
            "placeholder": "Nome da variável para guardar o texto"
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

    # Aponta para o dict central de execution_context.
    # Todos os blocos que fazem ExtractTextBlock._context[...] continuam funcionando.
    _context: dict = _ctx.get()

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        selector  = params.get("selector", "").strip()
        var_name  = params.get("variable_name", "texto_extraido").strip() or "texto_extraido"
        try:
            timeout = int(params.get("timeout", 10))
        except ValueError:
            timeout = 10

        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )

            # Tenta .text primeiro; se vier vazio usa innerText via JS
            text = element.text.strip()
            if not text:
                text = driver.execute_script("return arguments[0].innerText;", element)
                if text:
                    text = text.strip()

            # Se ainda vazio, tenta textContent (para elementos ocultos ou com CSS visibility)
            if not text:
                text = driver.execute_script("return arguments[0].textContent;", element)
                if text:
                    text = text.strip()

            ExtractTextBlock._context[var_name] = text or ""

            if text:
                return {
                    "success": True,
                    "message": f"Texto extraído → {var_name}: \"{text[:80]}{'...' if len(text) > 80 else ''}\"",
                    "data": {"variable": var_name, "value": text}
                }
            else:
                return {
                    "success": True,
                    "message": f"Elemento encontrado mas sem texto visível → {var_name}: \"\" (elemento pode ter texto em imagem ou ser vazio)",
                    "data": {"variable": var_name, "value": ""}
                }

        except Exception as e:
            return {"success": False, "message": f"Erro ao extrair texto de '{selector}': {str(e).split('Stacktrace')[0].strip()}"}

    @classmethod
    def get_context(cls) -> dict:
        return cls._context

    @classmethod
    def clear_context(cls):
        cls._context.clear()