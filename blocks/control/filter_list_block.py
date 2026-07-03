from blocks.base_block import BaseBlock


class FilterListBlock(BaseBlock):
    name = "Filtrar Lista"
    description = (
        "Filtra os itens de uma lista por uma condição e salva o resultado "
        "em uma nova variável. Aceita condições como: maior que, contém, começa com, etc."
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
            "name":        "condition_type",
            "label":       "Condição",
            "type":        "str",
            "required":    True,
            "default":     "item_contains",
            "placeholder": (
                "item_equals | item_not_equals | item_contains | item_not_contains | "
                "item_starts_with | item_ends_with | "
                "item_greater | item_less | item_not_empty | item_empty"
            ),
        },
        {
            "name":        "condition_value",
            "label":       "Valor de comparação",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: 10  ou  texto  (deixe vazio para item_empty / item_not_empty)",
        },
        {
            "name":        "output_variable",
            "label":       "Salvar resultado em",
            "type":        "str",
            "required":    True,
            "default":     "lista_filtrada",
            "placeholder": "Ex: lista_filtrada",
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        from blocks.browser.extract_text import ExtractTextBlock

        input_var  = params.get("input_variable", "").strip()
        ctype      = params.get("condition_type", "item_contains").strip()
        cvalue     = params.get("condition_value", "").strip()
        output_var = params.get("output_variable", "lista_filtrada").strip()

        raw = ExtractTextBlock._context.get(input_var)
        if raw is None:
            return {"success": False, "message": f"Variável '{input_var}' não encontrada no contexto."}

        if isinstance(raw, str):
            import json as _json
            try:
                raw = _json.loads(raw)
            except Exception:
                raw = [item.strip() for item in raw.split(",") if item.strip()]

        if not isinstance(raw, list):
            return {"success": False, "message": f"'{input_var}' não é uma lista (tipo: {type(raw).__name__})."}

        def _matches(item) -> bool:
            s = str(item)
            v = cvalue
            try:
                if ctype == "item_equals":
                    return s.strip().lower() == v.strip().lower()
                elif ctype == "item_not_equals":
                    return s.strip().lower() != v.strip().lower()
                elif ctype == "item_contains":
                    return v.lower() in s.lower()
                elif ctype == "item_not_contains":
                    return v.lower() not in s.lower()
                elif ctype == "item_starts_with":
                    return s.lower().startswith(v.lower())
                elif ctype == "item_ends_with":
                    return s.lower().endswith(v.lower())
                elif ctype == "item_greater":
                    return float(s) > float(v)
                elif ctype == "item_less":
                    return float(s) < float(v)
                elif ctype == "item_not_empty":
                    return s.strip() != ""
                elif ctype == "item_empty":
                    return s.strip() == ""
            except (ValueError, TypeError):
                pass
            return False

        filtered = [item for item in raw if _matches(item)]
        ExtractTextBlock._context[output_var] = filtered

        return {
            "success": True,
            "message": f"✓ Filtrados {len(filtered)}/{len(raw)} itens → '{output_var}'",
            "data": {"filtered_count": len(filtered), "total": len(raw)},
        }
