"""
Contexto de execução centralizado do PyFlow RPA.

Todos os blocos que leem/escrevem variáveis de execução operam sobre este
dicionário. O Runner limpa o contexto no início de cada execução, garantindo
que variáveis de uma run não contaminem a próxima.

Uso nos blocos (não muda nada — ExtractTextBlock._context aponta aqui):
    from blocks.browser.extract_text import ExtractTextBlock
    ExtractTextBlock._context["minha_var"] = valor   # continua funcionando

Uso no runner:
    import engine.execution_context as ctx
    ctx.clear()          # limpa antes de cada execução
    ctx.get()            # retorna o dict atual

Expressões suportadas em {{...}}:
    {{variavel}}              → substituição simples
    {{variavel.chave}}        → acesso a dict/atributo (dot notation)
    {{len(variavel)}}         → avaliação de expressão Python segura
    {{variavel.upper()}}      → métodos de string
    {{round(valor, 2)}}       → funções matemáticas
"""
import re
from engine.asset_manager import AssetManager

# Dict único compartilhado por toda a execução
_store: dict = {}

# Builtins permitidos na avaliação de expressões
_SAFE_BUILTINS = {
    "len": len, "str": str, "int": int, "float": float, "bool": bool,
    "round": round, "abs": abs, "min": min, "max": max, "sum": sum,
    "sorted": sorted, "list": list, "dict": dict, "tuple": tuple, "set": set,
    "range": range, "enumerate": enumerate, "zip": zip,
    "isinstance": isinstance, "type": type, "repr": repr,
    "True": True, "False": False, "None": None,
    "upper": str.upper, "lower": str.lower,  # atalhos diretos
}

# Padrão de variável/dot-notation pura (sem chamadas de função)
_SIMPLE_VAR_RE = re.compile(r'^[\w]+(\.\w+)*$')


def get() -> dict:
    """Retorna o dict de variáveis da execução atual."""
    return _store


def clear():
    """Limpa todas as variáveis. Deve ser chamado antes de cada nova execução."""
    _store.clear()


def _resolve_expr(expr: str, context: dict) -> str:
    """
    Resolve uma expressão {{expr}}:
    - Se for variável simples ou dot-notation → lookup direto
    - Caso contrário → avalia como expressão Python com builtins seguros
    """
    expr = expr.strip()

    if expr.startswith("ASSET:"):
        return None  # tratado separadamente

    # Variável simples ou dot notation: {{var}} / {{var.chave}}
    if _SIMPLE_VAR_RE.match(expr):
        parts = expr.split(".")
        if parts[0] not in context:
            raise ValueError(f"Variável não encontrada no contexto: '{parts[0]}'")
        val = context[parts[0]]
        for p in parts[1:]:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                raise ValueError(f"Atributo '{p}' não encontrado em '{expr}'")
        return str(val)

    # Expressão Python — avalia com contexto + builtins seguros
    try:
        local_ns = {**_SAFE_BUILTINS, **context}
        result = eval(expr, {"__builtins__": {}}, local_ns)  # noqa: S307
        return str(result)
    except Exception as e:
        raise ValueError(f"Erro ao avaliar expressão '{{{{ {expr} }}}}': {e}") from e


def resolve_params(params: dict, context: dict = None) -> dict:
    """
    Substitui tokens dinâmicos nos valores de parâmetros.
      {{ASSET:nome}}        → busca no arquivo de credenciais/configurações
      {{variavel}}          → busca nas variáveis de execução
      {{len(variavel)}}     → avalia expressão Python (builtins seguros)
      {{variavel.upper()}}  → métodos de string/objeto
    """
    if context is None:
        context = _store

    resolved = {}
    for key, value in params.items():
        if key == "nota":
            continue
        if not isinstance(value, str):
            resolved[key] = value
            continue

        def asset_replacer(match):
            asset_key = match.group(1).strip()
            val = AssetManager.get_asset(asset_key)
            return str(val) if val is not None else match.group(0)

        temp = re.sub(r"\{\{ASSET:(.+?)\}\}", asset_replacer, value)

        def context_replacer(match, _ctx=context):
            expr = match.group(1).strip()
            if expr.startswith("ASSET:"):
                return match.group(0)
            return _resolve_expr(expr, _ctx)

        resolved[key] = re.sub(r"\{\{(.+?)\}\}", context_replacer, temp)

    return resolved
