import re
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock


class TextManipulationBlock(BaseBlock):
    name = "Manipular Texto"
    description = "Aplica operações de texto em uma variável: substituir, maiúsculas, minúsculas, trim, extrair com regex, dividir, juntar, contar e mais."
    category = "Controle"

    params_schema = [
        {
            "name": "input_variable",
            "label": "Variável de entrada",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: texto_extraido, url_atual"
        },
        {
            "name": "operation",
            "label": "Operação",
            "type": "str",
            "required": True,
            "default": "upper",
            "placeholder": "upper, lower, trim, replace, regex_extract, regex_replace, split, join, count, contains, starts_with, ends_with, substring, length"
        },
        {
            "name": "param1",
            "label": "Parâmetro 1 (depende da operação)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "replace: texto antigo | regex_extract: padrão | split: separador | substring: início"
        },
        {
            "name": "param2",
            "label": "Parâmetro 2 (depende da operação)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "replace: texto novo | join: separador | substring: fim"
        },
        {
            "name": "output_variable",
            "label": "Salvar resultado como variável",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Deixe vazio para sobrescrever a variável de entrada"
        }
    ]

    OPERATIONS = {
        "upper", "lower", "trim", "replace", "regex_extract",
        "regex_replace", "split", "join", "count", "contains",
        "starts_with", "ends_with", "substring", "length"
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        input_var  = params.get("input_variable", "").strip()
        operation  = params.get("operation", "").strip().lower()
        param1     = params.get("param1", "")
        param2     = params.get("param2", "")
        output_var = params.get("output_variable", "").strip() or input_var

        if operation not in self.OPERATIONS:
            ops = ", ".join(sorted(self.OPERATIONS))
            return {"success": False, "message": f"Operação '{operation}' inválida. Use: {ops}"}

        # Busca o valor no contexto
        context = ExtractTextBlock._context
        raw_value = context.get(input_var, "")

        # Se for lista, converte para string quando necessário
        if isinstance(raw_value, list):
            input_value = raw_value
        else:
            input_value = str(raw_value)

        try:
            result = self._apply_operation(operation, input_value, param1, param2)
        except Exception as e:
            return {"success": False, "message": f"Erro na operação '{operation}': {str(e)}"}

        # Salva resultado no contexto
        context[output_var] = result

        # Preview do resultado
        preview = str(result)[:60] + ("..." if len(str(result)) > 60 else "")
        return {
            "success": True,
            "message": f"'{operation}' → {output_var}: \"{preview}\"",
            "data": {"variable": output_var, "value": result}
        }

    def _apply_operation(self, op: str, value, param1: str, param2: str):
        # Garante string para operações que precisam
        str_value = str(value) if not isinstance(value, str) else value

        if op == "upper":
            return str_value.upper()

        elif op == "lower":
            return str_value.lower()

        elif op == "trim":
            return str_value.strip()

        elif op == "replace":
            if not param1:
                raise ValueError("Parâmetro 1 obrigatório: texto a substituir")
            return str_value.replace(param1, param2)

        elif op == "regex_extract":
            if not param1:
                raise ValueError("Parâmetro 1 obrigatório: padrão regex")
            match = re.search(param1, str_value)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
            return ""

        elif op == "regex_replace":
            if not param1:
                raise ValueError("Parâmetro 1 obrigatório: padrão regex")
            return re.sub(param1, param2, str_value)

        elif op == "split":
            sep = param1 if param1 else ","
            return [v.strip() for v in str_value.split(sep)]

        elif op == "join":
            if not isinstance(value, list):
                raise ValueError("A variável de entrada deve ser uma lista para usar 'join'")
            sep = param1 if param1 else ", "
            return sep.join(str(v) for v in value)

        elif op == "count":
            if param1:
                return str(str_value.count(param1))
            return str(len(str_value))

        elif op == "contains":
            return str(param1.lower() in str_value.lower()) if param1 else "False"

        elif op == "starts_with":
            return str(str_value.startswith(param1)) if param1 else "False"

        elif op == "ends_with":
            return str(str_value.endswith(param1)) if param1 else "False"

        elif op == "substring":
            try:
                start = int(param1) if param1 else 0
                end   = int(param2) if param2 else None
                return str_value[start:end]
            except ValueError:
                raise ValueError("Parâmetros de substring devem ser números inteiros")

        elif op == "length":
            if isinstance(value, list):
                return str(len(value))
            return str(len(str_value))

        return str_value
