import time
import pyautogui
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock

class LocateImageBlock(BaseBlock):
    name = "Localizar Imagem na Tela"
    description = "Procura por uma imagem (template) na tela e retorna as coordenadas."
    category = "Visão Computacional"
    params_schema = [
        {
            "name": "image_path",
            "label": "Caminho da Imagem",
            "type": "file",
            "required": True,
            "placeholder": "Caminho do .png para buscar"
        },
        {
            "name": "confidence",
            "label": "Confiança (0.1 a 1.0)",
            "type": "float",
            "required": False,
            "default": 0.8,
            "placeholder": "Ex: 0.8"
        },
        {
            "name": "variable_name",
            "label": "Salvar Coordenadas em",
            "type": "str",
            "required": True,
            "default": "pos_imagem",
            "placeholder": "Ex: btn_pos"
        }
    ]

    def execute(self, params: dict) -> dict:
        img_path = params.get("image_path")
        conf = float(params.get("confidence", 0.8))
        var_name = params.get("variable_name")

        try:
            # Note: OpenCV is highly recommended for confidence to work
            pos = pyautogui.locateCenterOnScreen(img_path, confidence=conf)
            if pos:
                ExtractTextBlock._context[var_name] = {"x": pos.x, "y": pos.y}
                return {"success": True, "message": f"Imagem encontrada em {pos.x}, {pos.y}", "data": {"pos": pos}}
            else:
                return {"success": False, "message": "Imagem não encontrada na tela."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao localizar imagem: {e}"}

class GetPixelColorBlock(BaseBlock):
    name = "Obter Cor do Pixel"
    description = "Retorna a cor HEX de um pixel em coordenadas específicas."
    category = "Visão Computacional"
    params_schema = [
        {"name": "x", "label": "Posição X", "type": "int", "required": True},
        {"name": "y", "label": "Posição Y", "type": "int", "required": True},
        {"name": "variable_name", "label": "Salvar HEX em", "type": "str", "required": True, "default": "pixel_color"}
    ]

    def execute(self, params: dict) -> dict:
        x, y = int(params["x"]), int(params["y"])
        var_name = params["variable_name"]
        
        try:
            color = pyautogui.pixel(x, y)
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            ExtractTextBlock._context[var_name] = hex_color
            return {"success": True, "message": f"Cor no pixel ({x},{y}): {hex_color}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao obter cor: {e}"}

class WaitPixelColorBlock(BaseBlock):
    name = "Aguardar Cor no Pixel"
    description = "Pausa a execução até que um pixel mude para a cor desejada."
    category = "Visão Computacional"
    params_schema = [
        {"name": "x", "label": "Posição X", "type": "int", "required": True},
        {"name": "y", "label": "Posição Y", "type": "int", "required": True},
        {"name": "expected_color", "label": "Cor HEX Esperada", "type": "str", "required": True, "placeholder": "#FF0000"},
        {"name": "timeout", "label": "Timeout (segundos)", "type": "int", "default": 30}
    ]

    def execute(self, params: dict) -> dict:
        x, y = int(params["x"]), int(params["y"])
        expected = params["expected_color"].lower()
        timeout = int(params.get("timeout", 30))
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            color = pyautogui.pixel(x, y)
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            if hex_color.lower() == expected:
                return {"success": True, "message": f"Cor detectada no pixel ({x},{y})"}
            time.sleep(0.5)
            
        return {"success": False, "message": f"Timeout: Cor {expected} não detectada em ({x},{y})"}
