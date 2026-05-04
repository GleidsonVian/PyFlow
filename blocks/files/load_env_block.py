import os
import re
import csv
import engine.execution_context as ctx
from blocks.base_block import BaseBlock


class LoadEnvBlock(BaseBlock):
    name        = "Carregar Variáveis (.env / .csv)"
    description = "Carrega variáveis de um arquivo .env ou .csv para o contexto de execução"
    category    = "Arquivos"

    params_schema = [
        {
            "name": "filepath", "label": "Caminho do arquivo",
            "type": "str", "required": True, "default": "",
            "placeholder": "vars.env  ou  dados.csv",
        },
        {
            "name": "prefix", "label": "Prefixo das variáveis (opcional)",
            "type": "str", "required": False, "default": "",
            "placeholder": "ex: env_ → env_USUARIO",
        },
        {
            "name": "csv_key_col", "label": "CSV: coluna de chave",
            "type": "str", "required": False, "default": "key",
        },
        {
            "name": "csv_val_col", "label": "CSV: coluna de valor",
            "type": "str", "required": False, "default": "value",
        },
    ]

    def execute(self, params: dict) -> dict:
        filepath    = params.get("filepath", "").strip()
        prefix      = params.get("prefix", "").strip()
        csv_key_col = params.get("csv_key_col", "key").strip() or "key"
        csv_val_col = params.get("csv_val_col", "value").strip() or "value"

        if not os.path.isfile(filepath):
            return {"success": False, "message": f"Arquivo não encontrado: {filepath}"}

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".csv":
                loaded = self._load_csv(filepath, csv_key_col, csv_val_col)
            else:
                loaded = self._load_env(filepath)
        except Exception as e:
            return {"success": False, "message": f"Erro ao ler arquivo: {e}"}

        store = ctx.get()
        for k, v in loaded.items():
            store[f"{prefix}{k}"] = v

        return {
            "success": True,
            "message": f"{len(loaded)} variável(eis) carregada(s) de {os.path.basename(filepath)}",
            "data": {"loaded_keys": list(loaded.keys())},
        }

    def _load_env(self, filepath: str) -> dict:
        result = {}
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)', line)
                if m:
                    key, val = m.group(1), m.group(2)
                    val = val.strip('"').strip("'")
                    result[key] = val
        return result

    def _load_csv(self, filepath: str, key_col: str, val_col: str) -> dict:
        result = {}
        with open(filepath, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if key_col in row and val_col in row:
                    result[row[key_col]] = row[val_col]
        return result
