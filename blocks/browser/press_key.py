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
            "name": "key",
            "label": "Tecla",
            "type": "str",
            "required": True,
            "default": "Enter",
            "placeholder": "Enter, Tab, Escape, ArrowDown, F5..."
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