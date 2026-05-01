import os
from datetime import datetime
from blocks.base_block import BaseBlock


class SaveTextBlock(BaseBlock):
    name = "Salvar em TXT"
    description = "Salva um texto ou valor de variável em um arquivo .txt. Ideal para registrar dados extraídos."
    category = "Arquivos"

    params_schema = [
        {
            "name": "content",
            "label": "Conteúdo a salvar",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: {{texto_extraido}} ou texto fixo"
        },
        {
            "name": "filepath",
            "label": "Caminho do arquivo",
            "type": "str",
            "required": False,
            "default": "saida/resultado.txt",
            "placeholder": "Ex: saida/resultado.txt"
        },
        {
            "name": "mode",
            "label": "Modo (overwrite = sobrescrever / append = adicionar ao final)",
            "type": "str",
            "required": False,
            "default": "append",
            "placeholder": "overwrite ou append"
        },
        {
            "name": "add_timestamp",
            "label": "Adicionar timestamp em cada linha",
            "type": "bool",
            "required": False,
            "default": False
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        content       = params.get("content", "").strip()
        filepath      = params.get("filepath", "saida/resultado.txt").strip() or "saida/resultado.txt"
        mode          = params.get("mode", "append").strip().lower()
        add_timestamp = params.get("add_timestamp", False)

        if mode not in ("overwrite", "append"):
            mode = "append"

        file_mode = "w" if mode == "overwrite" else "a"

        try:
            # Cria pasta se não existir
            folder = os.path.dirname(filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)

            line = content
            if add_timestamp:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                line = f"[{ts}] {content}"

            with open(filepath, file_mode, encoding="utf-8") as f:
                f.write(line + "\n")

            action = "sobrescrito" if mode == "overwrite" else "atualizado"
            return {
                "success": True,
                "message": f"Arquivo {action}: {filepath}",
                "data": {"filepath": filepath, "content": content}
            }

        except Exception as e:
            return {"success": False, "message": f"Erro ao salvar arquivo: {str(e)}"}
