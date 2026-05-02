"""
Bloco de clipboard do PyFlow RPA.
Copia e cola texto do clipboard do sistema operacional.
Coloque em: blocks/system/clipboard_block.py
"""
import subprocess
import sys
from blocks.base_block import BaseBlock


class ClipboardBlock(BaseBlock):
    name        = "Clipboard"
    description = "Lê ou escreve no clipboard do sistema operacional. Copia texto para o clipboard, lê o conteúdo atual ou limpa."
    category    = "Sistema"

    params_schema = [
        {
            "name":        "action",
            "label":       "Ação",
            "type":        "str",
            "required":    True,
            "default":     "copy",
            "placeholder": "copy = copiar para clipboard | paste = ler do clipboard | clear = limpar"
        },
        {
            "name":        "value",
            "label":       "Texto a copiar (somente para action=copy)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Texto ou {{variavel}} a copiar para o clipboard"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar conteúdo como variável (somente para action=paste)",
            "type":        "str",
            "required":    False,
            "default":     "clipboard_texto",
            "placeholder": "Nome da variável onde salvar o texto lido"
        },
    ]

    ACTIONS = {"copy", "paste", "clear"}

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        action   = params.get("action", "copy").strip().lower()
        value    = params.get("value", "")
        var_name = params.get("variable_name", "clipboard_texto").strip() or "clipboard_texto"

        if action not in self.ACTIONS:
            return {"success": False, "message": f"Ação '{action}' inválida. Use: copy, paste, clear"}

        try:
            import pyperclip
        except ImportError:
            return {"success": False, "message": "pyperclip não instalado. Rode: pip install pyperclip"}

        try:
            if action == "copy":
                if not value:
                    return {"success": False, "message": "Valor obrigatório para action=copy."}
                pyperclip.copy(str(value))
                preview = str(value)[:60] + ("..." if len(str(value)) > 60 else "")
                return {"success": True, "message": f"Copiado para clipboard: \"{preview}\""}

            elif action == "paste":
                text = pyperclip.paste()
                from blocks.browser.extract_text import ExtractTextBlock
                ExtractTextBlock._context[var_name] = text
                preview = text[:60] + ("..." if len(text) > 60 else "")
                return {"success": True, "message": f"Lido do clipboard → '{var_name}': \"{preview}\""}

            elif action == "clear":
                pyperclip.copy("")
                return {"success": True, "message": "Clipboard limpo"}

        except Exception as e:
            return {"success": False, "message": f"Erro no clipboard: {str(e)}"}
