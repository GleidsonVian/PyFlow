from blocks.base_block import BaseBlock

class WebhookTriggerBlock(BaseBlock):
    name = "Gatilho: Webhook"
    description = "Transforma este fluxo em uma API. Ele será executado sempre que receber uma requisição HTTP POST no endpoint configurado."
    category = "Gatilhos"

    params_schema = [
        {
            "name": "path",
            "label": "Caminho do Endpoint",
            "type": "str",
            "required": True,
            "default": "meu-fluxo",
            "placeholder": "Ex: iniciar-vendas"
        },
        {
            "name": "save_payload",
            "label": "Salvar JSON recebido na variável",
            "type": "str",
            "required": False,
            "default": "webhook_data",
            "placeholder": "webhook_data"
        }
    ]

    def execute(self, params: dict) -> dict:
        import engine.execution_context as ctx

        path     = params.get("path", "meu-fluxo").strip()
        var_name = params.get("save_payload", "webhook_data").strip() or "webhook_data"

        store   = ctx.get()
        payload = store.get("webhook_payload", {})

        # Salva o payload completo na variável configurada
        store[var_name] = payload

        # Também expõe cada campo de primeiro nível como webhook_CAMPO
        if isinstance(payload, dict):
            for k, v in payload.items():
                store[f"webhook_{k}"] = str(v) if not isinstance(v, (list, dict)) else v

        fields = list(payload.keys()) if isinstance(payload, dict) else []
        detail = f"  Campos: {', '.join(fields)}" if fields else "  (payload vazio)"

        return {
            "success": True,
            "message": f"Webhook recebido em /{path} → {var_name}{detail}",
        }
