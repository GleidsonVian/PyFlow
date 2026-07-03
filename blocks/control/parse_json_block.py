import json as _json

from blocks.base_block import BaseBlock


class ParseJsonBlock(BaseBlock):
    name = "Parse JSON"
    description = (
        "Extrai campos de uma string JSON e salva cada campo como uma variável "
        "individual no contexto. Suporta JSON simples e aninhado com notação de ponto."
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "json_variable",
            "label":       "Variável com o JSON (ou JSON literal)",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": 'Ex: resposta_api  ou  {"nome": "João", "idade": 30}',
        },
        {
            "name":        "prefix",
            "label":       "Prefixo das variáveis geradas",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": 'Ex: dados  →  dados_nome, dados_idade  (deixe vazio para sem prefixo)',
        },
        {
            "name":        "fields",
            "label":       "Campos específicos (opcional)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "nome, idade, endereco.cidade  (vazio = todos os campos raiz)",
        },
        {
            "name":        "save_full",
            "label":       "Também salvar o objeto completo como variável",
            "type":        "bool",
            "required":    False,
            "default":     False,
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        from blocks.browser.extract_text import ExtractTextBlock

        json_var   = params.get("json_variable", "").strip()
        prefix     = params.get("prefix", "").strip()
        fields_raw = params.get("fields", "").strip()
        save_full  = bool(params.get("save_full", False))

        # Resolve o JSON: variável do contexto ou literal
        ctx = ExtractTextBlock._context
        raw = ctx.get(json_var, json_var)  # tenta como variável, cai no literal

        if isinstance(raw, (dict, list)):
            data = raw
        else:
            try:
                data = _json.loads(str(raw))
            except _json.JSONDecodeError as e:
                return {"success": False, "message": f"JSON inválido: {e}"}

        def _prefix(key):
            return f"{prefix}_{key}" if prefix else key

        def _dot_get(obj, path: str):
            """Acessa valor por notação de ponto: 'endereco.cidade'"""
            parts = path.split(".")
            val = obj
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return None
            return val

        saved = []

        if fields_raw:
            # Salva apenas os campos solicitados
            for field in [f.strip() for f in fields_raw.split(",") if f.strip()]:
                val = _dot_get(data, field) if isinstance(data, dict) else None
                var_name = _prefix(field.replace(".", "_"))
                ctx[var_name] = val
                saved.append(var_name)
        elif isinstance(data, dict):
            # Salva todos os campos raiz
            for key, val in data.items():
                var_name = _prefix(key)
                ctx[var_name] = val
                saved.append(var_name)
        else:
            # Lista → salva como variável única
            var_name = _prefix("lista")
            ctx[var_name] = data
            saved.append(var_name)

        if save_full:
            full_name = _prefix("json") if prefix else "json_parsed"
            ctx[full_name] = data
            saved.append(full_name)

        return {
            "success": True,
            "message": f"✓ Parse JSON: {len(saved)} variável(is) criada(s): {', '.join(saved)}",
            "data": {"variables": saved, "count": len(saved)},
        }
