import time
import pyautogui
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock

class GetMousePositionBlock(BaseBlock):
    name = "Obter Posição do Mouse"
    description = "Pausa a execução por alguns segundos e captura as coordenadas X e Y do cursor do mouse."
    category = "Sistema"
    params_schema = [
        {
            "name": "variable_name",
            "label": "Salvar em",
            "type": "str",
            "required": True,
            "default": "posicao_mouse",
            "placeholder": "Ex: pos"
        },
        {
            "name": "delay",
            "label": "Tempo para posicionar o mouse (segundos)",
            "type": "float",
            "required": False,
            "default": 3.0,
            "placeholder": "Ex: 3"
        }
    ]

    def execute(self, params: dict) -> dict:
        var_name = params.get("variable_name", "posicao_mouse")
        delay = float(params.get("delay", 3.0))

        if delay > 0:
            # Poderíamos colocar um log aqui se o runner suportasse feedback em tempo real
            time.sleep(delay)

        try:
            x, y = pyautogui.position()
            # Salva como dicionário para fácil acesso via {{posicao_mouse.x}}
            pos_dict = {"x": x, "y": y, "string": f"{x},{y}"}
            ExtractTextBlock._context[var_name] = pos_dict
            
            return {
                "success": True, 
                "message": f"Coordenadas capturadas: X={x}, Y={y}. Salvas em '{{{{{var_name}}}}}'",
                "data": pos_dict
            }
        except Exception as e:
            return {"success": False, "message": f"Erro ao capturar posição: {e}"}
