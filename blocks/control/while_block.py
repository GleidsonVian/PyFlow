from blocks.base_block import BaseBlock


class WhileBlock(BaseBlock):
    name = "Enquanto (While)"
    description = (
        "Repete os blocos internos enquanto uma condição for verdadeira. "
        "A condição é reavaliada a cada iteração. "
        "Use 'Máximo de iterações' para evitar loops infinitos. "
        "Sempre finalize com 'Fim do Enquanto'."
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "condition_type",
            "label":       "Tipo de condição",
            "type":        "str",
            "required":    True,
            "default":     "variable_less",
            "placeholder": (
                "variable_equals | variable_not_equals | "
                "variable_contains | variable_not_contains | "
                "variable_greater | variable_less | "
                "variable_empty | variable_not_empty"
            ),
        },
        {
            "name":        "variable_name",
            "label":       "Nome da variável",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: pagina_atual",
        },
        {
            "name":        "expected_value",
            "label":       "Valor de comparação",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: 10  (para 'pagina_atual < 10')",
        },
        {
            "name":        "max_iterations",
            "label":       "Máximo de iterações (segurança)",
            "type":        "str",
            "required":    False,
            "default":     "100",
            "placeholder": "Padrão: 100 — evita loop infinito",
        },
        {
            "name":        "delay_between",
            "label":       "Pausa entre iterações (segundos)",
            "type":        "str",
            "required":    False,
            "default":     "0",
            "placeholder": "0",
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        ctype    = params.get("condition_type", "variable_less").strip()
        var_name = params.get("variable_name", "").strip()
        expected = params.get("expected_value", "").strip()

        try:
            max_iter = int(params.get("max_iterations", 100))
        except ValueError:
            max_iter = 100
        try:
            delay = float(params.get("delay_between", 0))
        except ValueError:
            delay = 0.0

        # ── Avalia a condição (mesma lógica do IfBlock) ────────────────
        from blocks.browser.extract_text import ExtractTextBlock
        raw = ExtractTextBlock._context.get(var_name, "")
        val = str(raw)
        condition_met = False
        label = ""

        try:
            if ctype == "variable_equals":
                condition_met = val.strip().lower() == expected.strip().lower()
                label = f"'{var_name}' == '{expected}'"
            elif ctype == "variable_not_equals":
                condition_met = val.strip().lower() != expected.strip().lower()
                label = f"'{var_name}' != '{expected}'"
            elif ctype == "variable_contains":
                condition_met = expected.lower() in val.lower()
                label = f"'{var_name}' contém '{expected}'"
            elif ctype == "variable_not_contains":
                condition_met = expected.lower() not in val.lower()
                label = f"'{var_name}' não contém '{expected}'"
            elif ctype == "variable_greater":
                condition_met = float(val) > float(expected)
                label = f"'{var_name}' ({val}) > {expected}"
            elif ctype == "variable_less":
                condition_met = float(val) < float(expected)
                label = f"'{var_name}' ({val}) < {expected}"
            elif ctype == "variable_empty":
                condition_met = val.strip() == ""
                label = f"'{var_name}' está vazio"
            elif ctype == "variable_not_empty":
                condition_met = val.strip() != ""
                label = f"'{var_name}' não está vazio"
            else:
                return {"success": False, "message": f"Tipo de condição desconhecido: '{ctype}'"}

        except (ValueError, TypeError) as e:
            return {"success": False, "message": f"Erro de comparação numérica: {e}"}

        icon = "↻" if condition_met else "✓"
        status = "CONTINUA" if condition_met else "ENCERRA"
        return {
            "success": True,
            "message": f"{icon} Enquanto: {label} → {status}",
            "data": {
                "while":         True,
                "condition_met": condition_met,
                "max_iterations": max_iter,
                "delay_between": delay,
                # guarda os params para reavaliação pelo runner
                "condition_type": ctype,
                "variable_name":  var_name,
                "expected_value": expected,
            },
        }
