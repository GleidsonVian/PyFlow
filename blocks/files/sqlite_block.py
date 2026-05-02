"""
Bloco de banco de dados SQLite do PyFlow RPA.
Coloque em: blocks/files/sqlite_block.py
"""
import sqlite3
import os
from blocks.base_block import BaseBlock


class SQLiteBlock(BaseBlock):
    name        = "Banco de Dados (SQLite)"
    description = "Executa queries SQL em um banco SQLite local. Suporta SELECT (salva resultado como variável), INSERT, UPDATE, DELETE e CREATE TABLE."
    category    = "Arquivos"

    params_schema = [
        {
            "name":        "database",
            "label":       "Arquivo do banco (.db)",
            "type":        "str",
            "required":    True,
            "default":     "dados/banco.db",
            "placeholder": "Ex: dados/meu_banco.db"
        },
        {
            "name":        "query",
            "label":       "Query SQL",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: SELECT * FROM produtos WHERE preco < 100"
        },
        {
            "name":        "params",
            "label":       "Parâmetros da query (separados por |)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: {{nome}}|{{preco}} — usa ? na query"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar resultado como variável (SELECT)",
            "type":        "str",
            "required":    False,
            "default":     "db_resultado",
            "placeholder": "Nome da variável para armazenar linhas retornadas"
        },
        {
            "name":        "row_variable",
            "label":       "Variável para primeira linha",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: primeiro_registro (salva dict da 1ª linha)"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        database   = params.get("database", "dados/banco.db").strip()
        query      = params.get("query", "").strip()
        raw_params = params.get("params", "").strip()
        var_name   = params.get("variable_name", "db_resultado").strip() or "db_resultado"
        row_var    = params.get("row_variable", "").strip()

        if not query:
            return {"success": False, "message": "Query SQL é obrigatória."}

        # Cria pasta do banco se não existir
        folder = os.path.dirname(database)
        if folder:
            os.makedirs(folder, exist_ok=True)

        # Monta parâmetros posicionais
        sql_params = [p.strip() for p in raw_params.split("|") if p.strip()] if raw_params else []

        try:
            with sqlite3.connect(database) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, sql_params)

                operation = query.strip().upper().split()[0]

                if operation == "SELECT":
                    return self._handle_select(cursor, var_name, row_var, database)
                else:
                    return self._handle_write(conn, cursor, operation)

        except sqlite3.Error as e:
            return {"success": False, "message": f"Erro SQL: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Erro: {str(e)}"}

    def _handle_select(self, cursor, var_name: str, row_var: str, database: str) -> dict:
        from blocks.browser.extract_text import ExtractTextBlock
        context = ExtractTextBlock._context

        rows = cursor.fetchall()
        # Converte Row objects em dicts
        result = [dict(row) for row in rows]

        context[var_name]              = result
        context[f"{var_name}_total"]   = str(len(result))
        context[f"{var_name}_colunas"] = list(result[0].keys()) if result else []

        if row_var and result:
            context[row_var] = result[0]
            # Expande campos da primeira linha como variáveis individuais
            for col, val in result[0].items():
                context[f"{row_var}_{col}"] = str(val)

        preview = str(result[:2])[:80] + ("..." if len(result) > 2 else "")
        return {
            "success": True,
            "message": f"SELECT retornou {len(result)} linha(s) → '{var_name}'",
            "data":    {"rows": result, "count": len(result)}
        }

    def _handle_write(self, conn, cursor, operation: str) -> dict:
        conn.commit()
        affected = cursor.rowcount
        msgs = {
            "INSERT": f"INSERT executado — {affected} linha(s) inserida(s)",
            "UPDATE": f"UPDATE executado — {affected} linha(s) atualizada(s)",
            "DELETE": f"DELETE executado — {affected} linha(s) removida(s)",
            "CREATE": "CREATE TABLE executado com sucesso",
            "DROP":   "DROP executado com sucesso",
        }
        msg = msgs.get(operation, f"{operation} executado com sucesso")
        return {"success": True, "message": msg}
