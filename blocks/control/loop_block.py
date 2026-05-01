from blocks.base_block import BaseBlock


class LoopBlock(BaseBlock):
    name = "Loop (Repetir)"
    description = "Marca o início de um loop. Os próximos N blocos serão repetidos X vezes."
    category = "Controle"

    params_schema = [
        {
            "name": "times",
            "label": "Repetições",
            "type": "str",
            "required": True,
            "default": "3",
            "placeholder": "Número de vezes para repetir"
        },
        {
            "name": "blocks_count",
            "label": "Quantos blocos incluir no loop",
            "type": "str",
            "required": True,
            "default": "1",
            "placeholder": "Blocos seguintes que fazem parte do loop"
        },
        {
            "name": "delay_between",
            "label": "Pausa entre repetições (segundos)",
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

        try:
            times = int(params.get("times", 3))
            blocks_count = int(params.get("blocks_count", 1))
            delay = float(params.get("delay_between", 0))
        except ValueError:
            return {"success": False, "message": "Valores inválidos. Use números inteiros para repetições e blocos."}

        if times < 1:
            return {"success": False, "message": "O número de repetições deve ser maior que 0."}
        if blocks_count < 1:
            return {"success": False, "message": "O número de blocos no loop deve ser maior que 0."}

        return {
            "success": True,
            "message": f"Loop configurado: {times}x repetindo {blocks_count} bloco(s)",
            "data": {
                "loop": True,
                "times": times,
                "blocks_count": blocks_count,
                "delay_between": delay
            }
        }
