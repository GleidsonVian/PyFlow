"""
Bloco de execução de JavaScript no navegador do PyFlow RPA.
Coloque em: blocks/browser/execute_script.py
"""
from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ExecuteScriptBlock(BaseBlock):
    name        = "Executar JavaScript"
    description = "Executa código JavaScript diretamente no navegador via driver.execute_script(). Permite rolar para elementos, clicar em elementos ocultos, ler variáveis JS da página e simular eventos customizados."
    category    = "Navegador"

    params_schema = [
        {
            "name":        "script",
            "label":       "Código JavaScript",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: return document.title; | window.scrollTo(0, 500); | return window.minha_var;"
        },
        {
            "name":        "selector",
            "label":       "Seletor CSS do elemento (opcional — passa como arguments[0])",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: #meu-botao — disponível no script como arguments[0]"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar retorno como variável (opcional)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: js_resultado — salva o return do script"
        },
    ]

    # Scripts prontos que o usuário pode copiar como base
    EXAMPLES = """
# Rolar até elemento:
arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});

# Clicar em elemento oculto:
arguments[0].click();

# Remover atributo disabled:
arguments[0].removeAttribute('disabled');

# Ler variável JS da página:
return window.minha_variavel;

# Ler título da página:
return document.title;

# Rolar para topo:
window.scrollTo(0, 0);

# Rolar para baixo:
window.scrollTo(0, document.body.scrollHeight);

# Pegar texto de elemento oculto:
return arguments[0].innerText;

# Definir valor em campo (bypassa React/Vue):
var el = arguments[0];
var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
nativeSetter.call(el, 'novo valor');
el.dispatchEvent(new Event('input', { bubbles: true }));
""".strip()

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        script   = params.get("script", "").strip()
        selector = params.get("selector", "").strip()
        var_name = params.get("variable_name", "").strip()

        if not script:
            return {"success": False, "message": "Código JavaScript é obrigatório."}

        try:
            if selector:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                result = driver.execute_script(script, element)
            else:
                result = driver.execute_script(script)

            # Salva retorno no contexto se solicitado
            if var_name and result is not None:
                from blocks.browser.extract_text import ExtractTextBlock
                ExtractTextBlock._context[var_name] = result

            # Monta preview do resultado
            if result is None:
                msg = "JavaScript executado com sucesso"
            else:
                preview = str(result)[:80] + ("..." if len(str(result)) > 80 else "")
                msg = f"JavaScript executado → retornou: \"{preview}\""
                if var_name:
                    msg += f" → salvo em '{var_name}'"

            return {"success": True, "message": msg, "data": {"result": result}}

        except Exception as e:
            err = str(e).split("Stacktrace")[0].strip()
            return {"success": False, "message": f"Erro ao executar JavaScript: {err}"}