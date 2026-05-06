from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock

KEY_MAP = {
    "Enter":     Keys.ENTER,
    "Tab":       Keys.TAB,
    "Escape":    Keys.ESCAPE,
    "Backspace": Keys.BACK_SPACE,
    "Delete":    Keys.DELETE,
    "Space":     Keys.SPACE,
    "ArrowUp":   Keys.ARROW_UP,
    "ArrowDown": Keys.ARROW_DOWN,
    "ArrowLeft": Keys.ARROW_LEFT,
    "ArrowRight":Keys.ARROW_RIGHT,
    "Home":      Keys.HOME,
    "End":       Keys.END,
    "PageUp":    Keys.PAGE_UP,
    "PageDown":  Keys.PAGE_DOWN,
    "F5":        Keys.F5,
}


class PressKeyBlock(BaseBlock):
    name = "Pressionar Tecla"
    description = "Pressiona uma tecla especial em um elemento ou na página inteira"
    category = "Navegador"

    params_schema = [
        {
            "name":    "key",
            "label":   "Tecla",
            "type":    "select",
            "required": True,
            "default": "Enter",
            "options": [
                {"value": "Enter",      "label": "Enter",      "description": "Confirma ação, submete formulário ou ativa botão focado."},
                {"value": "Tab",        "label": "Tab",        "description": "Avança o foco para o próximo campo ou elemento interativo."},
                {"value": "Escape",     "label": "Escape",     "description": "Cancela ação, fecha modais, popups ou dropdowns."},
                {"value": "Space",      "label": "Space",      "description": "Pressiona Espaço — ativa checkboxes e botões focados."},
                {"value": "Backspace",  "label": "Backspace",  "description": "Apaga o caractere à esquerda do cursor."},
                {"value": "Delete",     "label": "Delete",     "description": "Apaga o caractere à direita do cursor."},
                {"value": "ArrowUp",    "label": "↑ ArrowUp",    "description": "Move o cursor ou seleção para cima."},
                {"value": "ArrowDown",  "label": "↓ ArrowDown",  "description": "Move o cursor ou seleção para baixo."},
                {"value": "ArrowLeft",  "label": "← ArrowLeft",  "description": "Move o cursor para a esquerda."},
                {"value": "ArrowRight", "label": "→ ArrowRight", "description": "Move o cursor para a direita."},
                {"value": "Home",       "label": "Home",       "description": "Vai para o início da linha ou do campo."},
                {"value": "End",        "label": "End",        "description": "Vai para o fim da linha ou do campo."},
                {"value": "PageUp",     "label": "PageUp",     "description": "Rola a página para cima (uma tela inteira)."},
                {"value": "PageDown",   "label": "PageDown",   "description": "Rola a página para baixo (uma tela inteira)."},
                {"value": "F5",         "label": "F5",         "description": "Atualiza / recarrega a página atual."},
            ],
        },
        {
            "name": "selector",
            "label": "Seletor CSS (opcional — vazio = body)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Deixe vazio para pressionar na página inteira"
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

        key_name = params.get("key", "Enter").strip()
        selector = params.get("selector", "").strip()
        try:
            timeout = int(params.get("timeout", 10))
        except ValueError:
            timeout = 10

        key = KEY_MAP.get(key_name)
        if not key:
            return {"success": False, "message": f"Tecla '{key_name}' não reconhecida. Use: {', '.join(KEY_MAP.keys())}"}

        try:
            if selector:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            else:
                element = driver.find_element(By.TAG_NAME, "body")

            element.send_keys(key)
            target = f"em '{selector}'" if selector else "na página"
            return {"success": True, "message": f"Tecla '{key_name}' pressionada {target}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao pressionar tecla: {str(e)}"}