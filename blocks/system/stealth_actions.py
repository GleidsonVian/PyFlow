import time
import random
import pyautogui
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock

class ClickCoordinateBlock(BaseBlock):
    name = "Clicar em Coordenada"
    description = "Move o mouse e clica em uma posição específica da tela com opções de stealth (humanização)."
    category = "Sistema"
    params_schema = [
        {"name": "x", "label": "Coordenada X", "type": "int", "required": True},
        {"name": "y", "label": "Coordenada Y", "type": "int", "required": True},
        {"name": "clicks", "label": "Número de cliques", "type": "int", "default": 1},
        {"name": "button", "label": "Botão (left/right/middle)", "type": "str", "default": "left"},
        {"name": "humanize", "label": "Modo Stealth (Humanizar)", "type": "bool", "default": True},
        {"name": "offset", "label": "Desvio aleatório (pixels)", "type": "int", "default": 3},
        {"name": "duration", "label": "Duração do movimento (segundos)", "type": "float", "default": 0.2}
    ]

    def execute(self, params: dict) -> dict:
        try:
            x = int(params.get("x", 0))
            y = int(params.get("y", 0))
            clicks = int(params.get("clicks", 1))
            button = params.get("button", "left").lower()
            humanize = bool(params.get("humanize", True))
            offset = int(params.get("offset", 3))
            duration = float(params.get("duration", 0.2))

            target_x = x
            target_y = y

            if humanize:
                # Adiciona variação aleatória para não clicar sempre no mesmo pixel
                target_x += random.randint(-offset, offset)
                target_y += random.randint(-offset, offset)
                # Varia a duração do movimento em +/- 20%
                duration *= random.uniform(0.8, 1.2)

            pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeInOutQuad if humanize else pyautogui.linear)
            pyautogui.click(x=target_x, y=target_y, clicks=clicks, button=button)

            return {
                "success": True, 
                "message": f"Clicou em ({target_x}, {target_y}) com o botão {button}. Stealth: {humanize}",
                "data": {"final_x": target_x, "final_y": target_y}
            }
        except Exception as e:
            return {"success": False, "message": f"Erro ao clicar: {e}"}

class KeyboardActionBlock(BaseBlock):
    name = "Ação de Teclado (Global)"
    description = "Pressiona teclas ou digita texto globalmente no sistema."
    category = "Sistema"
    params_schema = [
        {"name": "action", "label": "Ação (press/type/hotkey)", "type": "str", "default": "press"},
        {"name": "value", "label": "Tecla ou Texto", "type": "str", "required": True},
        {"name": "humanize", "label": "Humanizar digitação", "type": "bool", "default": True},
        {"name": "interval", "label": "Intervalo entre teclas (segundos)", "type": "float", "default": 0.1}
    ]

    def execute(self, params: dict) -> dict:
        try:
            action = params.get("action", "press").lower()
            value = params.get("value", "")
            humanize = bool(params.get("humanize", True))
            interval = float(params.get("interval", 0.1))

            if humanize:
                interval *= random.uniform(0.5, 1.5)

            if action == "press":
                pyautogui.press(value, interval=interval)
            elif action == "type":
                pyautogui.write(value, interval=interval)
            elif action == "hotkey":
                keys = [k.strip() for k in value.split("+")]
                pyautogui.hotkey(*keys)

            return {"success": True, "message": f"Executou ação de teclado: {action} ({value})"}
        except Exception as e:
            return {"success": False, "message": f"Erro no teclado: {e}"}
