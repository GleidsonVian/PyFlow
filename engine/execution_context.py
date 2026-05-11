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
"""
import re
from engine.asset_manager import AssetManager

# Dict único compartilhado por toda a execução
_store: dict = {}


def get() -> dict:
    """Retorna o dict de variáveis da execução atual."""
    return _store


def clear():
    """Limpa todas as variáveis. Deve ser chamado antes de cada nova execução."""
    _store.clear()


def resolve_params(params: dict, context: dict = None) -> dict:
    """
    Substitui tokens dinâmicos nos valores de parâmetros.
      {{ASSET:nome}}  → busca no arquivo de credenciais/configurações
      {{nome}}        → busca nas variáveis de execução
    """
    if context is None:
        context = _store

    resolved = {}
    for key, value in params.items():
        if key == "nota": # Ignora anotações
            continue
        if not isinstance(value, str):
            resolved[key] = value
            continue

        def asset_replacer(match):
            asset_key = match.group(1).strip()
            val = AssetManager.get_asset(asset_key)
            return str(val) if val is not None else match.group(0)

        temp = re.sub(r"\{\{ASSET:(.+?)\}\}", asset_replacer, value)

        def context_replacer(match):
            var_name = match.group(1).strip()
            if var_name.startswith("ASSET:"):
                return match.group(0)
            
            # Suporte a dot notation (ex: {{posicao.x}})
            parts = var_name.split(".")
            
            if parts[0] not in context:
                raise ValueError(f"Variável não encontrada no contexto: {parts[0]}")
            
            val = context.get(parts[0])
            
            if len(parts) == 1:
                return str(val)
            
            curr = val
            for i in range(1, len(parts)):
                p = parts[i]
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    path_so_far = ".".join(parts[:i+1])
                    raise ValueError(f"Atributo '{p}' não encontrado no caminho '{path_so_far}'")
            
            return str(curr)

        resolved[key] = re.sub(r"\{\{(.+?)\}\}", context_replacer, temp)

    return resolved
