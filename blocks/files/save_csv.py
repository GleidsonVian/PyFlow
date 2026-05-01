import csv
import os
from datetime import datetime
from blocks.base_block import BaseBlock


class SaveCsvBlock(BaseBlock):
    name = "Salvar em CSV"
    description = "Adiciona uma linha de dados a um arquivo CSV. Ideal para coletar dados extraídos de múltiplas páginas."
    category = "Arquivos"

    params_schema = [
        {
            "name": "filepath",
            "label": "Caminho do arquivo CSV",
            "type": "str",
            "required": False,
            "default": "saida/dados.csv",
            "placeholder": "Ex: saida/dados.csv"
        },
        {
            "name": "values",
            "label": "Valores (separados por |)",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: {{titulo}}|{{preco}}|{{url_atual}}"
        },
        {
            "name": "headers",
            "label": "Cabeçalhos (só na primeira vez, separados por |)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: Titulo|Preco|URL (deixe vazio para não criar cabeçalho)"
        },
        {
            "name": "delimiter",
            "label": "Delimitador",
            "type": "str",
            "required": False,
            "default": ",",
            "placeholder": ", ou ; ou |"
        },
        {
            "name": "add_timestamp",
            "label": "Adicionar coluna de timestamp",
            "type": "bool",
            "required": False,
            "default": False
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        filepath      = params.get("filepath", "saida/dados.csv").strip() or "saida/dados.csv"
        values_raw    = params.get("values", "").strip()
        headers_raw   = params.get("headers", "").strip()
        delimiter     = params.get("delimiter", ",").strip() or ","
        add_timestamp = params.get("add_timestamp", False)

        values = [v.strip() for v in values_raw.split("|")]

        try:
            folder = os.path.dirname(filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)

            file_exists = os.path.exists(filepath)

            with open(filepath, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=delimiter)

                # Escreve cabeçalho só se o arquivo é novo e headers foram definidos
                if not file_exists and headers_raw:
                    headers = [h.strip() for h in headers_raw.split("|")]
                    if add_timestamp:
                        headers = ["Timestamp"] + headers
                    writer.writerow(headers)

                # Escreve linha de dados
                row = values
                if add_timestamp:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row = [ts] + values

                writer.writerow(row)

            preview = " | ".join(values[:3])
            if len(values) > 3:
                preview += f" ... (+{len(values) - 3})"

            return {
                "success": True,
                "message": f"Linha salva em {filepath}: {preview}",
                "data": {"filepath": filepath, "row": values}
            }

        except Exception as e:
            return {"success": False, "message": f"Erro ao salvar CSV: {str(e)}"}
