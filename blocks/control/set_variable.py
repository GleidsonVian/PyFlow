"""
Bloco de variável do PyFlow RPA.
Define, incrementa, decrementa, concatena e manipula variáveis
sem precisar de scraping ou API.
Coloque em: blocks/control/set_variable.py
"""
from datetime import datetime
from blocks.base_block import BaseBlock


class SetVariableBlock(BaseBlock):
    name        = "Definir Variável"
    description = "Cria ou modifica variáveis no contexto sem precisar de scraping. Suporta: definir valor fixo, incrementar, decrementar, concatenar, data/hora atual e operações matemáticas."
    category    = "Controle"

    params_schema = [
        {
            "name":        "variable_name",
            "label":       "Nome da variável",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: contador, nome_completo, total"
        },
        {
            "name":    "operation",
            "label":   "Operação",
            "type":    "select",
            "required": True,
            "default": "set",
            "options": [
                {"value": "set",       "label": "= Definir valor",         "description": "Define a variável com o Valor informado. Sobrescreve qualquer valor anterior."},
                {"value": "increment", "label": "+ Incrementar",           "description": "Soma o Valor ao número atual da variável. Padrão: +1 se o campo Valor estiver vazio."},
                {"value": "decrement", "label": "- Decrementar",           "description": "Subtrai o Valor do número atual da variável. Padrão: -1 se o campo Valor estiver vazio."},
                {"value": "append",    "label": "⟶ Concatenar ao final",  "description": "Adiciona o Valor ao final do texto atual da variável (string append)."},
                {"value": "prepend",   "label": "⟵ Concatenar ao início", "description": "Adiciona o Valor antes do texto atual da variável (string prepend)."},
                {"value": "multiply",  "label": "× Multiplicar",           "description": "Multiplica o valor atual pelo Valor informado. Ex: variável=5, Valor=3 → 15."},
                {"value": "divide",    "label": "÷ Dividir",               "description": "Divide o valor atual pelo Valor informado. Retorna erro se Valor=0."},
                {"value": "now",       "label": "🕐 Data/hora atual",      "description": "Salva a data e hora atual na variável. Use o campo Formato para personalizar. Ex: %d/%m/%Y"},
                {"value": "clear",     "label": "🗑 Remover variável",     "description": "Remove a variável do contexto completamente. Ela deixará de existir."},
            ],
        },
        {
            "name":        "value",
            "label":       "Valor",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Valor a definir/usar. Aceita {{variavel}}"
        },
        {
            "name":        "format",
            "label":       "Formato (somente para operation=now)",
            "type":        "str",
            "required":    False,
            "default":     "%d/%m/%Y %H:%M:%S",
            "placeholder": "%d/%m/%Y | %H:%M:%S | %Y%m%d_%H%M%S"
        },
    ]

    OPERATIONS = {
        "set", "increment", "decrement", "append",
        "prepend", "multiply", "divide", "now", "clear"
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        from blocks.browser.extract_text import ExtractTextBlock
        context = ExtractTextBlock._context

        var_name  = params.get("variable_name", "").strip()
        operation = params.get("operation", "set").strip().lower()
        value     = params.get("value", "")
        fmt       = params.get("format", "%d/%m/%Y %H:%M:%S").strip()

        if not var_name:
            return {"success": False, "message": "Nome da variável é obrigatório."}

        if operation not in self.OPERATIONS:
            valid = ", ".join(sorted(self.OPERATIONS))
            return {"success": False, "message": f"Operação '{operation}' inválida. Use: {valid}"}

        current = context.get(var_name, "")

        try:
            if operation == "set":
                context[var_name] = value
                return {"success": True, "message": f"'{var_name}' = \"{value}\""}

            elif operation == "increment":
                step = float(value) if value else 1
                try:
                    new_val = float(str(current)) + step
                    # Exibe como inteiro se não tiver parte decimal
                    context[var_name] = str(int(new_val)) if new_val == int(new_val) else str(new_val)
                except ValueError:
                    context[var_name] = str(step)
                return {"success": True, "message": f"'{var_name}' incrementado → {context[var_name]}"}

            elif operation == "decrement":
                step = float(value) if value else 1
                try:
                    new_val = float(str(current)) - step
                    context[var_name] = str(int(new_val)) if new_val == int(new_val) else str(new_val)
                except ValueError:
                    context[var_name] = str(-step)
                return {"success": True, "message": f"'{var_name}' decrementado → {context[var_name]}"}

            elif operation == "append":
                context[var_name] = str(current) + str(value)
                preview = str(context[var_name])[:50]
                return {"success": True, "message": f"'{var_name}' → \"{preview}\""}

            elif operation == "prepend":
                context[var_name] = str(value) + str(current)
                preview = str(context[var_name])[:50]
                return {"success": True, "message": f"'{var_name}' → \"{preview}\""}

            elif operation == "multiply":
                if not value:
                    return {"success": False, "message": "Valor obrigatório para multiply."}
                new_val = float(str(current)) * float(value)
                context[var_name] = str(int(new_val)) if new_val == int(new_val) else str(new_val)
                return {"success": True, "message": f"'{var_name}' × {value} = {context[var_name]}"}

            elif operation == "divide":
                if not value:
                    return {"success": False, "message": "Valor obrigatório para divide."}
                divisor = float(value)
                if divisor == 0:
                    return {"success": False, "message": "Divisão por zero não é permitida."}
                new_val = float(str(current)) / divisor
                context[var_name] = str(int(new_val)) if new_val == int(new_val) else f"{new_val:.4f}"
                return {"success": True, "message": f"'{var_name}' ÷ {value} = {context[var_name]}"}

            elif operation == "now":
                context[var_name] = datetime.now().strftime(fmt)
                return {"success": True, "message": f"'{var_name}' = \"{context[var_name]}\""}

            elif operation == "clear":
                if var_name in context:
                    del context[var_name]
                return {"success": True, "message": f"Variável '{var_name}' removida do contexto"}

        except Exception as e:
            return {"success": False, "message": f"Erro na operação '{operation}': {str(e)}"}

        return {"success": False, "message": f"Operação '{operation}' não executada."}
