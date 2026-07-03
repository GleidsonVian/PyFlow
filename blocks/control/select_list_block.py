from blocks.base_block import BaseBlock


class SelectListBlock(BaseBlock):
    name = "Transformar Lista (Select)"
    description = (
        "Aplica uma expressão Python a cada item de uma lista e retorna uma nova lista "
        "com os resultados. Use 'item' para referenciar o elemento atual. "
        "Ex: item.upper()  |  item * 2  |  item['nome']"
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "input_variable",
            "label":       "Variável com a lista",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: minha_lista",
        },
        {
            "name":        "expression",
            "label":       "Expressão por item (use 'item')",
            "type":        "str",
            "required":    True,
            "default":     "item",
            "placeholder": "Ex: item.upper()  |  str(item).strip()  |  item['nome']",
        },
        {
            "name":        "output_variable",
            "label":       "Salvar resultado em",
            "type":        "str",
            "required":    True,
            "default":     "lista_transformada",
            "placeholder": "Ex: lista_transformada",
        },
        {
            "name":        "skip_errors",
            "label":       "Ignorar erros por item (continuar nos demais)",
            "type":        "bool",
            "required":    False,
            "default":     True,
        },
    ]

    # Builtins seguros disponíveis na expressão
    _SAFE_BUILTINS = {
        "str": str, "int": int, "float": float, "bool": bool,
        "len": len, "round": round, "abs": abs,
        "upper": str.upper, "lower": str.lower, "strip": str.strip,
        "min": min, "max": max, "sum": sum,
        "list": list, "dict": dict, "tuple": tuple,
        "True": True, "False": False, "None": None,
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        from blocks.browser.extract_text import ExtractTextBlock

        input_var  = params.get("input_variable", "").strip()
        expression = params.get("expression", "item").strip()
        output_var = params.get("output_variable", "lista_transformada").strip()
        skip_errs  = bool(params.get("skip_errors", True))

        raw = ExtractTextBlock._context.get(input_var)
        if raw is None:
            return {"success": False, "message": f"Variável '{input_var}' não encontrada."}

        if isinstance(raw, str):
            import json as _json
            try:
                raw = _json.loads(raw)
            except Exception:
                raw = [i.strip() for i in raw.split(",") if i.strip()]

        if not isinstance(raw, list):
            return {"success": False, "message": f"'{input_var}' não é uma lista (tipo: {type(raw).__name__})."}

        result = []
        item_errors = 0

        for item in raw:  # noqa: F841 — 'item' usado no eval
            try:
                ns = {**self._SAFE_BUILTINS, "item": item}
                transformed = eval(expression, {"__builtins__": {}}, ns)  # noqa: S307
                result.append(transformed)
            except Exception as e:
                if skip_errs:
                    item_errors += 1
                    result.append(None)
                else:
                    return {
                        "success": False,
                        "message": f"Erro ao transformar item '{item}': {e}",
                    }

        ExtractTextBlock._context[output_var] = result

        msg = f"✓ {len(result)} itens transformados → '{output_var}'"
        if item_errors:
            msg += f" ({item_errors} com erro → None)"

        return {
            "success": True,
            "message": msg,
            "data": {"count": len(result), "errors": item_errors},
        }
