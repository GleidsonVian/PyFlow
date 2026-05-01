"""
Bloco de espera inteligente do PyFlow RPA.
Aguarda condições específicas antes de prosseguir.
Coloque em: blocks/browser/smart_wait.py
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class SmartWaitBlock(BaseBlock):
    name        = "Espera Inteligente"
    description = "Aguarda uma condição específica antes de prosseguir: elemento aparecer/sumir, URL mudar, texto aparecer, página carregar. Mais robusto que o Aguardar simples."
    category    = "Navegador"

    params_schema = [
        {
            "name":        "condition",
            "label":       "Condição a aguardar",
            "type":        "str",
            "required":    True,
            "default":     "element_visible",
            "placeholder": "element_visible | element_clickable | element_hidden | element_exists | url_contains | url_equals | text_in_element | text_in_page | page_loaded | element_count"
        },
        {
            "name":        "selector",
            "label":       "Seletor CSS (para condições de elemento)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: .btn-submit, #resultado, .loading"
        },
        {
            "name":        "value",
            "label":       "Valor esperado (para condições de texto/URL)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: /dashboard (URL), Sucesso (texto), 5 (contagem)"
        },
        {
            "name":        "timeout",
            "label":       "Tempo máximo de espera (segundos)",
            "type":        "str",
            "required":    False,
            "default":     "15",
            "placeholder": "15"
        },
        {
            "name":        "poll_interval",
            "label":       "Intervalo de verificação (segundos)",
            "type":        "str",
            "required":    False,
            "default":     "0.5",
            "placeholder": "0.5"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar resultado como variável (opcional)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: elemento_encontrado (salva True/False)"
        },
    ]

    CONDITIONS = {
        "element_visible",
        "element_clickable",
        "element_hidden",
        "element_exists",
        "url_contains",
        "url_equals",
        "text_in_element",
        "text_in_page",
        "page_loaded",
        "element_count",
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        condition    = params.get("condition", "element_visible").strip().lower()
        selector     = params.get("selector", "").strip()
        value        = params.get("value", "").strip()
        var_name     = params.get("variable_name", "").strip()

        try:
            timeout       = float(params.get("timeout", 15))
            poll_interval = float(params.get("poll_interval", 0.5))
        except ValueError:
            timeout, poll_interval = 15.0, 0.5

        if condition not in self.CONDITIONS:
            valid = ", ".join(sorted(self.CONDITIONS))
            return {"success": False, "message": f"Condição '{condition}' inválida.\nUse: {valid}"}

        try:
            result, message = self._wait(driver, condition, selector, value, timeout, poll_interval)
        except Exception as e:
            return {"success": False, "message": f"Erro na espera: {str(e).split('Stacktrace')[0].strip()}"}

        # Salva no contexto se solicitado
        if var_name:
            from blocks.browser.extract_text import ExtractTextBlock
            ExtractTextBlock._context[var_name] = str(result)

        if result:
            return {"success": True,  "message": message}
        else:
            return {"success": False, "message": message}

    def _wait(self, driver, condition: str, selector: str, value: str,
              timeout: float, poll: float) -> tuple[bool, str]:

        wait = WebDriverWait(driver, timeout, poll_frequency=poll)

        # ── Condições de elemento ─────────────────────────────────────
        if condition == "element_visible":
            if not selector:
                return False, "Seletor CSS obrigatório para element_visible."
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                return True, f"Elemento visível: {selector}"
            except Exception:
                return False, f"Timeout: elemento '{selector}' não ficou visível em {timeout}s"

        elif condition == "element_clickable":
            if not selector:
                return False, "Seletor CSS obrigatório para element_clickable."
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                return True, f"Elemento clicável: {selector}"
            except Exception:
                return False, f"Timeout: elemento '{selector}' não ficou clicável em {timeout}s"

        elif condition == "element_hidden":
            if not selector:
                return False, "Seletor CSS obrigatório para element_hidden."
            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
                return True, f"Elemento oculto/removido: {selector}"
            except Exception:
                return False, f"Timeout: elemento '{selector}' ainda visível após {timeout}s"

        elif condition == "element_exists":
            if not selector:
                return False, "Seletor CSS obrigatório para element_exists."
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return True, f"Elemento presente no DOM: {selector}"
            except Exception:
                return False, f"Timeout: elemento '{selector}' não apareceu em {timeout}s"

        # ── Condições de URL ──────────────────────────────────────────
        elif condition == "url_contains":
            if not value:
                return False, "Valor obrigatório para url_contains. Ex: /dashboard"
            try:
                wait.until(EC.url_contains(value))
                return True, f"URL contém '{value}': {driver.current_url}"
            except Exception:
                return False, f"Timeout: URL não contém '{value}' após {timeout}s. URL atual: {driver.current_url}"

        elif condition == "url_equals":
            if not value:
                return False, "Valor obrigatório para url_equals."
            try:
                wait.until(EC.url_to_be(value))
                return True, f"URL igual a '{value}'"
            except Exception:
                return False, f"Timeout: URL não mudou para '{value}' em {timeout}s. Atual: {driver.current_url}"

        # ── Condições de texto ────────────────────────────────────────
        elif condition == "text_in_element":
            if not selector:
                return False, "Seletor CSS obrigatório para text_in_element."
            if not value:
                return False, "Valor (texto esperado) obrigatório para text_in_element."
            try:
                wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, selector), value))
                return True, f"Texto '{value}' encontrado em: {selector}"
            except Exception:
                return False, f"Timeout: texto '{value}' não apareceu em '{selector}' após {timeout}s"

        elif condition == "text_in_page":
            if not value:
                return False, "Valor (texto a buscar) obrigatório para text_in_page."
            deadline = time.time() + timeout
            while time.time() < deadline:
                if value.lower() in driver.page_source.lower():
                    return True, f"Texto '{value}' encontrado na página"
                time.sleep(poll)
            return False, f"Timeout: texto '{value}' não apareceu na página após {timeout}s"

        # ── Condição de carregamento ──────────────────────────────────
        elif condition == "page_loaded":
            deadline = time.time() + timeout
            while time.time() < deadline:
                state = driver.execute_script("return document.readyState")
                if state == "complete":
                    return True, f"Página carregada (readyState=complete)"
                time.sleep(poll)
            return False, f"Timeout: página não carregou em {timeout}s"

        # ── Condição de contagem de elementos ─────────────────────────
        elif condition == "element_count":
            if not selector:
                return False, "Seletor CSS obrigatório para element_count."
            try:
                expected = int(value) if value else 1
            except ValueError:
                return False, f"Valor deve ser um número inteiro para element_count. Recebido: '{value}'"

            deadline = time.time() + timeout
            while time.time() < deadline:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) >= expected:
                    return True, f"{len(elements)} elemento(s) '{selector}' encontrado(s)"
                time.sleep(poll)
            atual = len(driver.find_elements(By.CSS_SELECTOR, selector))
            return False, f"Timeout: esperava {expected} elemento(s) '{selector}', encontrou {atual} após {timeout}s"

        return False, f"Condição '{condition}' não implementada."
