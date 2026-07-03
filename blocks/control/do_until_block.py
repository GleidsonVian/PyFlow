from blocks.base_block import BaseBlock


class DoUntilBlock(BaseBlock):
    name = "Repetir Até (Do Until)"
    description = (
        "Executa os blocos internos pelo menos uma vez e repete até que "
        "a condição seja verdadeira. Diferente do Enquanto, a condição é "
        "verificada APÓS cada execução. Sempre finalize com 'Fim do Repetir Até'."
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "condition_type",
            "label":       "Parar quando",
            "type":        "str",
            "required":    True,
            "default":     "variable_equals",
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
            "placeholder": "Ex: tentativas",
        },
        {
            "name":        "expected_value",
            "label":       "Valor de comparação",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: sucesso",
        },
        {
            "name":        "max_iterations",
            "label":       "Máximo de iterações (segurança)",
            "type":        "str",
            "required":    False,
            "default":     "100",
            "placeholder": "Padrão: 100",
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

        ctype    = params.get("condition_type", "variable_equals").strip()
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

        return {
            "success": True,
            "message": f"↺ Repetir Até: '{var_name}' {ctype} '{expected}' (máx {max_iter}x)",
            "data": {
                "do_until":       True,
                "max_iterations": max_iter,
                "delay_between":  delay,
                "condition_type": ctype,
                "variable_name":  var_name,
                "expected_value": expected,
            },
        }

    def _check_condition(self, ctype, var_name, expected) -> bool:
        from blocks.browser.extract_text import ExtractTextBlock
        raw = ExtractTextBlock._context.get(var_name, "")
        val = str(raw)
        try:
            if ctype == "variable_equals":
                return val.strip().lower() == expected.strip().lower()
            elif ctype == "variable_not_equals":
                return val.strip().lower() != expected.strip().lower()
            elif ctype == "variable_contains":
                return expected.lower() in val.lower()
            elif ctype == "variable_not_contains":
                return expected.lower() not in val.lower()
            elif ctype == "variable_greater":
                return float(val) > float(expected)
            elif ctype == "variable_less":
                return float(val) < float(expected)
            elif ctype == "variable_empty":
                return val.strip() == ""
            elif ctype == "variable_not_empty":
                return val.strip() != ""
        except (ValueError, TypeError):
            pass
        return False
