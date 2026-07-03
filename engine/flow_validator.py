"""
Valida um fluxo antes de executar.
Retorna lista de issues: {"level": "error"|"warning", "step": int, "block": str, "msg": str}
"""
import re


_CSS_OBVIOUSLY_BROKEN = re.compile(r'["\'].*["\']|xpath\s*=|//[a-z]', re.IGNORECASE)

_VAR_REF = re.compile(r'\{\{([^}]+)\}\}')


def validate_flow(steps: list) -> list[dict]:
    issues = []
    defined_vars: set[str] = set()

    for i, step in enumerate(steps):
        block_instance = step.get("block_instance")
        params         = step.get("params", {})
        block_name     = block_instance.name if block_instance else step.get("block", "?")

        # 1. Parâmetros obrigatórios vazios
        if block_instance:
            errors = block_instance.validate_params(dict(params))
            for err in errors:
                issues.append({
                    "level": "error", "step": i + 1,
                    "block": block_name, "msg": err,
                })

        # 2. Variáveis referenciadas antes de serem definidas
        for val in params.values():
            if not isinstance(val, str):
                continue
            for ref in _VAR_REF.findall(val):
                ref = ref.strip()
                if ref.startswith("ASSET:"):
                    continue
                # notação de ponto: http_resposta.bairro → base é http_resposta
                base = ref.split(".")[0].split("[")[0]
                if base not in defined_vars and ref not in defined_vars:
                    issues.append({
                        "level": "warning", "step": i + 1,
                        "block": block_name,
                        "msg": f"Variável '{{{{ {ref} }}}}' usada antes de ser definida",
                    })

        # 3. Rastreia variáveis definidas por este bloco
        # Abordagem genérica: qualquer campo cujo nome sugere "saída de variável"
        _OUTPUT_KEYS = (
            "variable_name", "output_variable", "var_name",
            "save_as", "result_variable", "output_var",
        )
        for key in _OUTPUT_KEYS:
            var = params.get(key, "")
            if isinstance(var, str):
                var = var.strip()
                if var:
                    defined_vars.add(var)

        # LoadEnvBlock: não sabemos as keys em tempo de validação estática
        # ParseJsonBlock: pode gerar N variáveis com prefixo — aceita sem rastrear

        # 4. Seletores CSS com sintaxe XPath misturada
        for key in ("selector",):
            val = params.get(key, "")
            if isinstance(val, str) and _CSS_OBVIOUSLY_BROKEN.search(val):
                issues.append({
                    "level": "warning", "step": i + 1,
                    "block": block_name,
                    "msg": f"Seletor pode conter sintaxe XPath em campo CSS: '{val[:60]}'",
                })

    return issues
