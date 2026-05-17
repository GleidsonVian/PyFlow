import os
from blocks.base_block import BaseBlock
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

class TextToSpeechBlock(BaseBlock):
    name = "Texto para Áudio (TTS)"
    description = "Converte um texto em arquivo de áudio MP3 usando o Google TTS."
    category = "Sistema"

    params_schema = [
        {
            "name": "text",
            "label": "Texto para converter",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: Olá, bem-vindo ao PyFlow!"
        },
        {
            "name": "filename",
            "label": "Nome do arquivo de saída (.mp3)",
            "type": "str",
            "required": True,
            "default": "audiobook.mp3",
            "placeholder": "Ex: capitulo1.mp3"
        },
        {
            "name": "language",
            "label": "Idioma",
            "type": "select",
            "required": True,
            "default": "pt",
            "options": [
                {"value": "pt", "label": "Português"},
                {"value": "en", "label": "Inglês"},
                {"value": "es", "label": "Espanhol"},
                {"value": "fr", "label": "Francês"}
            ]
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        if gTTS is None:
            return {"success": False, "message": "Biblioteca 'gTTS' não instalada. Por favor, instale-a via terminal: pip install gTTS"}

        text = params.get("text", "").strip()
        filename = params.get("filename", "audiobook.mp3").strip()
        lang = params.get("language", "pt")

        if not text:
            return {"success": False, "message": "O texto para conversão está vazio."}

        try:
            # Garante que a pasta de destino exista
            dest_dir = os.path.dirname(filename)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            tts = gTTS(text=text, lang=lang)
            tts.save(filename)
            
            return {
                "success": True,
                "message": f"Áudio gerado com sucesso: {filename} (Idioma: {lang})",
                "data": {"audio_path": os.path.abspath(filename)}
            }
        except Exception as e:
            return {"success": False, "message": f"Erro ao gerar áudio: {str(e)}"}
