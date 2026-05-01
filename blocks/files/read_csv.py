import csv
import os
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock


class ReadCsvBlock(BaseBlock):
    name = "Ler CSV"
    description = "Lê um arquivo CSV e salva as linhas como lista no contexto para usar com For Each"
    category = "Arquivos"

    params_schema = [
        {
            "name": "filepath",
            "label": "Caminho do arquivo CSV",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: dados/lista.csv ou C:/pasta/arquivo.csv"
        },
        {
            "name": "column",
            "label": "Coluna a extrair (nome ou índice numérico)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "Ex: email, url, 0, 1"
        },
        {
            "name": "variable_name",
            "label": "Salvar lista como variável",
            "type": "str",
            "required": False,
            "default": "csv_linhas",
            "placeholder": "Nome da variável que receberá a lista"
        },
        {
            "name": "skip_header",
            "label": "Pular primeira linha (cabeçalho)",
            "type": "bool",
            "required": False,
            "default": True
        },
        {
            "name": "delimiter",
            "label": "Delimitador",
            "type": "str",
            "required": False,
            "default": ",",
            "placeholder": ", ou ; ou |"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        filepath    = params.get("filepath", "").strip()
        column      = params.get("column", "0").strip()
        var_name    = params.get("variable_name", "csv_linhas").strip() or "csv_linhas"
        skip_header = params.get("skip_header", True)
        delimiter   = params.get("delimiter", ",").strip() or ","

        if not os.path.exists(filepath):
            return {"success": False, "message": f"Arquivo não encontrado: {filepath}"}

        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)

            if not rows:
                return {"success": False, "message": "O arquivo CSV está vazio."}

            header = rows[0] if skip_header else None
            data_rows = rows[1:] if skip_header else rows

            # Determina índice da coluna
            col_index = None
            if column.isdigit():
                col_index = int(column)
            elif header and column in header:
                col_index = header.index(column)
            else:
                col_index = 0

            values = []
            for row in data_rows:
                if col_index < len(row):
                    values.append(row[col_index].strip())

            # Salva lista no contexto — for_each_block já sabe iterar listas
            ExtractTextBlock._context[var_name] = values
            # Também salva o primeiro valor direto para uso imediato
            if values:
                ExtractTextBlock._context[f"{var_name}_primeiro"] = values[0]
                ExtractTextBlock._context[f"{var_name}_total"] = str(len(values))

            return {
                "success": True,
                "message": f"CSV lido: {len(values)} linha(s) → variável '{var_name}'",
                "data": {"variable": var_name, "count": len(values), "values": values}
            }

        except Exception as e:
            return {"success": False, "message": f"Erro ao ler CSV: {str(e)}"}
