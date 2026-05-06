from blocks.base_block import BaseBlock


class ForEachBlock(BaseBlock):
    name = "Para Cada (For Each)"
    description = (
        "Itera sobre uma lista, executando os blocos seguintes para cada item. "
        "Adicione um bloco 'Fim do Para Cada' para marcar onde o loop termina. "
        "Use {{item_atual}} nos blocos internos para acessar o valor corrente."
    )
    category = "Controle"

    params_schema = [
        {
            "name": "items",
            "label": "Lista (separada por vírgula) ou nome de variável de lista",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: google.com, github.com  OU  minha_lista"
        },
        {
            "name": "variable_name",
            "label": "Variável de iteração",
            "type": "str",
            "required": False,
            "default": "item_atual",
            "placeholder": "Nome da variável que recebe o item atual"
        },
        {
            "name": "delay_between",
            "label": "Pausa entre iterações (segundos)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "0"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        items_param = params.get("items", "").strip()
        var_name    = params.get("variable_name", "item_atual").strip() or "item_atual"
        try:
            delay = float(params.get("delay_between", 0))
        except ValueError:
            delay = 0.0

        from blocks.browser.extract_text import ExtractTextBlock
        context = ExtractTextBlock._context

        if items_param in context and isinstance(context[items_param], list):
            items = context[items_param]
        else:
            items = [i.strip() for i in items_param.split(",") if i.strip()]

        if not items:
            return {"success": False, "message": "A lista de valores está vazia."}

        # Define o primeiro item para que blocos de preview já tenham acesso
        context[var_name] = items[0]

        return {
            "success": True,
            "message": f"Para Cada: {len(items)} item(s) → variável '{var_name}'",
            "data": {
                "foreach": True,
                "items": items,
                "variable_name": var_name,
                "delay_between": delay,
            }
        }
