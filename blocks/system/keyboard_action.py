"""
Bloco de interação com teclado e mouse do sistema operacional via PyAutoGUI.
Atua fora do navegador — controla qualquer janela ou aplicativo aberto.
Coloque em: blocks/system/keyboard_action.py
"""
import time
from blocks.base_block import BaseBlock


# Teclas especiais suportadas pelo pyautogui
SPECIAL_KEYS = [
    "enter", "tab", "escape", "space", "backspace", "delete",
    "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "ctrl", "alt", "shift", "win", "capslock", "numlock", "scrolllock",
    "printscreen", "insert", "pause",
]


class KeyboardActionBlock(BaseBlock):
    name = "Teclado do Sistema"
    description = "Interage com o teclado do sistema operacional via PyAutoGUI. Digita texto, pressiona teclas e combos (Ctrl+C, Alt+Tab...) em qualquer janela aberta."
    category = "Sistema"

    params_schema = [
        {
            "name": "action",
            "label": "Ação",
            "type": "str",
            "required": True,
            "default": "type",
            "placeholder": "type | press | hotkey | shortcut"
        },
        {
            "name": "value",
            "label": "Valor / Tecla(s)",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "type: texto a digitar | press: enter | hotkey: ctrl+c"
        },
        {
            "name": "interval",
            "label": "Intervalo entre teclas (segundos)",
            "type": "str",
            "required": False,
            "default": "0.05",
            "placeholder": "0.05 = 50ms entre cada tecla"
        },
        {
            "name": "delay_before",
            "label": "Aguardar antes de executar (segundos)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "Tempo para focar a janela alvo antes de digitar"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        action  = params.get("action", "type").strip().lower()
        value   = params.get("value", "").strip()
        try:
            interval     = float(params.get("interval", 0.05))
            delay_before = float(params.get("delay_before", 0))
        except ValueError:
            interval, delay_before = 0.05, 0

        if not value:
            return {"success": False, "message": "O campo 'Valor / Tecla(s)' é obrigatório."}

        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # Mover mouse ao canto superior esquerdo cancela
            pyautogui.PAUSE = 0.01
        except ImportError:
            return {"success": False, "message": "pyautogui não instalado. Rode: pip install pyautogui"}

        if delay_before > 0:
            time.sleep(delay_before)

        try:
            if action == "type":
                # Digita texto caractere por caractere
                pyautogui.typewrite(value, interval=interval)
                return {"success": True, "message": f"Texto digitado: \"{value[:50]}{'...' if len(value) > 50 else ''}\""}

            elif action == "press":
                # Pressiona uma tecla especial
                key = value.lower()
                if key not in SPECIAL_KEYS and len(key) > 1:
                    return {"success": False, "message": f"Tecla '{value}' não reconhecida. Teclas válidas: {', '.join(SPECIAL_KEYS[:10])}..."}
                pyautogui.press(key)
                return {"success": True, "message": f"Tecla pressionada: {value}"}

            elif action in ("hotkey", "shortcut"):
                # Pressiona combinação de teclas: ctrl+c, alt+tab, ctrl+shift+t...
                keys = [k.strip().lower() for k in value.replace("+", " ").split()]
                if not keys:
                    return {"success": False, "message": "Nenhuma tecla informada para o atalho."}
                pyautogui.hotkey(*keys)
                return {"success": True, "message": f"Atalho executado: {value}"}

            else:
                return {"success": False, "message": f"Ação '{action}' inválida. Use: type, press, hotkey"}

        except Exception as e:
            return {"success": False, "message": f"Erro ao executar ação de teclado: {str(e)}"}
