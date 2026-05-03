"""
Bloco OCR do PyFlow RPA.
Extrai texto de imagens usando pytesseract + Pillow.
Coloque em: blocks/system/ocr_block.py

Requisitos:
  pip install pytesseract pillow
  + Tesseract instalado no sistema:
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
    Linux:   sudo apt install tesseract-ocr tesseract-ocr-por
    Mac:     brew install tesseract
"""
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import os
from blocks.base_block import BaseBlock


class OcrBlock(BaseBlock):
    name        = "OCR (Extrair Texto de Imagem)"
    description = "Extrai texto de uma imagem usando pytesseract (Tesseract OCR). Suporta imagens locais, screenshots do canvas e recorte de região específica da imagem."
    category    = "Sistema"

    params_schema = [
        {
            "name":        "source",
            "label":       "Fonte da imagem",
            "type":        "str",
            "required":    True,
            "default":     "file",
            "placeholder": "file = arquivo local | screenshot = captura da tela agora | browser = screenshot do navegador"
        },
        {
            "name":        "filepath",
            "label":       "Caminho da imagem (para source=file)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: screenshots/captura.png | imagens/nota.jpg"
        },
        {
            "name":        "language",
            "label":       "Idioma do OCR",
            "type":        "str",
            "required":    False,
            "default":     "por",
            "placeholder": "por = Português | eng = Inglês | por+eng = ambos"
        },
        {
            "name":        "psm",
            "label":       "Modo de segmentação (PSM)",
            "type":        "str",
            "required":    False,
            "default":     "3",
            "placeholder": "3=auto | 6=bloco de texto | 7=linha única | 11=texto esparso | 13=linha bruta"
        },
        {
            "name":        "preprocess",
            "label":       "Pré-processamento da imagem",
            "type":        "str",
            "required":    False,
            "default":     "none",
            "placeholder": "none | grayscale | threshold | denoise"
        },
        {
            "name":        "crop",
            "label":       "Recortar região (left,top,right,bottom em pixels)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: 100,50,800,300 — vazio = imagem inteira"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar texto extraído como variável",
            "type":        "str",
            "required":    False,
            "default":     "ocr_texto",
            "placeholder": "Nome da variável para o texto extraído"
        },
        {
            "name":        "save_image",
            "label":       "Salvar imagem pré-processada (debug)",
            "type":        "bool",
            "required":    False,
            "default":     False
        },
    ]

    PSM_OPTIONS = {"3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"}
    PREPROCESS  = {"none", "grayscale", "threshold", "denoise"}
    SOURCES     = {"file", "screenshot", "browser"}

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        source     = params.get("source", "file").strip().lower()
        filepath   = params.get("filepath", "").strip()
        language   = params.get("language", "por").strip() or "por"
        psm        = params.get("psm", "3").strip() or "3"
        preprocess = params.get("preprocess", "none").strip().lower() or "none"
        crop_str   = params.get("crop", "").strip()
        var_name   = params.get("variable_name", "ocr_texto").strip() or "ocr_texto"
        save_img   = params.get("save_image", False)

        if source not in self.SOURCES:
            return {"success": False, "message": f"source inválido: '{source}'. Use: file, screenshot, browser"}
        if psm not in self.PSM_OPTIONS:
            return {"success": False, "message": f"PSM inválido: '{psm}'. Use: {', '.join(sorted(self.PSM_OPTIONS))}"}
        if preprocess not in self.PREPROCESS:
            return {"success": False, "message": f"preprocess inválido: '{preprocess}'. Use: {', '.join(self.PREPROCESS)}"}

        # Importa dependências
        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            return {"success": False, "message": f"Dependência não instalada: {e}\nRode: pip install pytesseract pillow"}

        # Verifica se tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            return {
                "success": False,
                "message": (
                    "Tesseract não encontrado no sistema.\n"
                    "Windows: baixe em https://github.com/UB-Mannheim/tesseract/wiki\n"
                    "Linux: sudo apt install tesseract-ocr tesseract-ocr-por\n"
                    "Mac: brew install tesseract"
                )
            }

        # Obtém a imagem
        try:
            image = self._get_image(source, filepath, Image)
        except Exception as e:
            return {"success": False, "message": f"Erro ao carregar imagem: {str(e)}"}

        # Recorta região se solicitado
        if crop_str:
            crop_result = self._crop_image(image, crop_str)
            if isinstance(crop_result, str):
                return {"success": False, "message": crop_result}
            image = crop_result

        # Aplica pré-processamento
        image = self._preprocess(image, preprocess)

        # Salva imagem de debug se solicitado
        if save_img:
            debug_path = "screenshots/ocr_debug.png"
            os.makedirs("screenshots", exist_ok=True)
            image.save(debug_path)

        # Executa OCR
        try:
            config   = f"--psm {psm}"
            raw_text = pytesseract.image_to_string(image, lang=language, config=config)
            text     = raw_text.strip()
        except Exception as e:
            return {"success": False, "message": f"Erro no OCR: {str(e)}"}

        # Salva no contexto
        from blocks.browser.extract_text import ExtractTextBlock
        context = ExtractTextBlock._context
        context[var_name]              = text
        context[f"{var_name}_linhas"]  = text.splitlines()
        context[f"{var_name}_total"]   = str(len(text))
        context[f"{var_name}_palavras"]= str(len(text.split()))

        if not text:
            return {
                "success": True,
                "message": f"OCR concluído mas nenhum texto encontrado — tente outro PSM ou preprocess"
            }

        preview = text[:80].replace("\n", " ") + ("..." if len(text) > 80 else "")
        return {
            "success": True,
            "message": f"OCR extraiu {len(text.split())} palavra(s) → '{var_name}': \"{preview}\"",
            "data":    {"text": text, "words": len(text.split()), "lines": len(text.splitlines())}
        }

    def _get_image(self, source: str, filepath: str, Image):
        if source == "file":
            if not filepath:
                raise ValueError("filepath é obrigatório para source=file")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
            return Image.open(filepath)

        if source == "screenshot":
            import pyautogui
            return pyautogui.screenshot()

        if source == "browser":
            from blocks.browser.open_browser import OpenBrowserBlock
            driver = OpenBrowserBlock.get_driver()
            if not driver:
                raise RuntimeError("Nenhum navegador aberto para source=browser")
            import io
            png_bytes = driver.get_screenshot_as_png()
            return Image.open(io.BytesIO(png_bytes))

    def _crop_image(self, image, crop_str: str):
        try:
            parts = [int(x.strip()) for x in crop_str.split(",")]
            if len(parts) != 4:
                return "crop deve ter 4 valores: left,top,right,bottom"
            return image.crop(tuple(parts))
        except ValueError:
            return f"crop inválido: '{crop_str}'. Use: left,top,right,bottom (ex: 100,50,800,300)"

    def _preprocess(self, image, mode: str):
        if mode == "none":
            return image

        # Converte para escala de cinza para todos os modos
        gray = image.convert("L")

        if mode == "grayscale":
            return gray

        if mode == "threshold":
            from PIL import ImageFilter
            # Binarização simples — melhora contraste para OCR
            return gray.point(lambda p: 255 if p > 128 else 0, "1").convert("L")

        if mode == "denoise":
            from PIL import ImageFilter
            return gray.filter(ImageFilter.MedianFilter(size=3))

        return image
