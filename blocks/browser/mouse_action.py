from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class MouseActionBlock(BaseBlock):
    name = "Ação de Mouse"
    description = "Executa ações avançadas de mouse: duplo clique, clique direito, hover, arrastar elemento, clicar por coordenadas."
    category = "Navegador"

    params_schema = [
        {
            "name": "action",
            "label": "Ação",
            "type": "str",
            "required": True,
            "default": "double_click",
            "placeholder": "double_click, right_click, hover, drag_and_drop, click_offset, move_to"
        },
        {
            "name": "selector",
            "label": "Seletor CSS do elemento alvo",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: .btn-submit, #menu-item (obrigatório para a maioria das ações)"
        },
        {
            "name": "target_selector",
            "label": "Seletor CSS do destino (só para drag_and_drop)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: #drop-zone (onde soltar o elemento)"
        },
        {
            "name": "offset_x",
            "label": "Offset X em pixels (para click_offset e move_to)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "Pixels horizontais a partir do elemento"
        },
        {
            "name": "offset_y",
            "label": "Offset Y em pixels (para click_offset e move_to)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "Pixels verticais a partir do elemento"
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

    ACTIONS = {
        "double_click", "right_click", "hover",
        "drag_and_drop", "click_offset", "move_to"
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        action        = params.get("action", "").strip().lower()
        selector      = params.get("selector", "").strip()
        target_sel    = params.get("target_selector", "").strip()
        try:
            offset_x = int(params.get("offset_x", 0))
            offset_y = int(params.get("offset_y", 0))
            timeout  = int(params.get("timeout", 10))
        except ValueError:
            offset_x, offset_y, timeout = 0, 0, 10

        if action not in self.ACTIONS:
            return {"success": False, "message": f"Ação '{action}' inválida. Use: {', '.join(sorted(self.ACTIONS))}"}

        try:
            actions = ActionChains(driver)

            if action == "double_click":
                if not selector:
                    return {"success": False, "message": "Seletor CSS obrigatório para double_click."}
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                actions.double_click(element).perform()
                return {"success": True, "message": f"Duplo clique em: {selector}"}

            elif action == "right_click":
                if not selector:
                    return {"success": False, "message": "Seletor CSS obrigatório para right_click."}
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                actions.context_click(element).perform()
                return {"success": True, "message": f"Clique direito em: {selector}"}

            elif action == "hover":
                if not selector:
                    return {"success": False, "message": "Seletor CSS obrigatório para hover."}
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                actions.move_to_element(element).perform()
                return {"success": True, "message": f"Hover em: {selector}"}

            elif action == "drag_and_drop":
                if not selector or not target_sel:
                    return {"success": False, "message": "Seletor de origem e destino obrigatórios para drag_and_drop."}
                source = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                target = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, target_sel))
                )
                actions.drag_and_drop(source, target).perform()
                return {"success": True, "message": f"Arrastado '{selector}' para '{target_sel}'"}

            elif action == "click_offset":
                if not selector:
                    return {"success": False, "message": "Seletor CSS obrigatório para click_offset."}
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                actions.move_to_element_with_offset(element, offset_x, offset_y).click().perform()
                return {"success": True, "message": f"Clique em offset ({offset_x}, {offset_y}) do elemento '{selector}'"}

            elif action == "move_to":
                if selector:
                    element = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    actions.move_to_element_with_offset(element, offset_x, offset_y).perform()
                    return {"success": True, "message": f"Mouse movido para offset ({offset_x}, {offset_y}) do elemento '{selector}'"}
                else:
                    actions.move_by_offset(offset_x, offset_y).perform()
                    return {"success": True, "message": f"Mouse movido para ({offset_x}, {offset_y})"}

        except Exception as e:
            return {"success": False, "message": f"Erro na ação '{action}': {str(e).split('Stacktrace')[0].strip()}"}
