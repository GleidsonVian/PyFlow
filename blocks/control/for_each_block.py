from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock


class ForEachBlock(BaseBlock):
    name = "Para Cada (For Each)"
    description = "Itera sobre uma lista de valores ou sobre uma variável de lista (ex: csv_linhas). Os próximos N blocos são executados para cada item."
    category = "Controle"

    params_schema = [
        {
            "name": "items",
            "label": "Lista de valores (separados por vírgula) ou nome de variável de lista",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: google.com, github.com  OU  csv_linhas"
        },
        {
            "name": "variable_name",
            "label": "Nome da variável de iteração",
            "type": "str",
            "required": False,
            "default": "item_atual",
            "placeholder": "Variável que recebe o valor atual a cada iteração"
        },
        {
            "name": "blocks_count",
            "label": "Quantos blocos incluir no loop",
            "type": "str",
            "required": True,
            "default": "1",
            "placeholder": "Blocos seguintes que fazem parte do For Each"
        },
        {
            "name": "delay_between",
            "label": "Pausa entre iterações (segundos)",
            "type": "str",
            "required": False,
            "default": "0",
            "placeholder": "0"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        items_param  = params.get("items", "").strip()
        var_name     = params.get("variable_name", "item_atual").strip() or "item_atual"
        try:
            blocks_count = int(params.get("blocks_count", 1))
            delay        = float(params.get("delay_between", 0))
        except ValueError:
            return {"success": False, "message": "Valores inválidos para blocos ou delay."}

        # Verifica se é uma variável de lista no contexto
        context = ExtractTextBlock._context
        if items_param in context and isinstance(context[items_param], list):
            items = context[items_param]
        else:
            # Trata como lista literal separada por vírgula
            items = [i.strip() for i in items_param.split(",") if i.strip()]

        if not items:
            return {"success": False, "message": "A lista de valores está vazia."}

        # Salva o primeiro item para inicializar
        ExtractTextBlock._context[var_name] = items[0]

        return {
            "success": True,
            "message": f"For Each: {len(items)} item(s) → variável '{var_name}'",
            "data": {
                "foreach": True,
                "items": items,
                "variable_name": var_name,
                "blocks_count": blocks_count,
                "delay_between": delay
            }
        }