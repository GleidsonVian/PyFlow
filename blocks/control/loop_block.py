from blocks.base_block import BaseBlock


class LoopBlock(BaseBlock):
    name = "Loop (Repetir)"
    description = (
        "Repete os blocos seguintes N vezes. "
        "Adicione um bloco 'Fim do Loop' para marcar onde o loop termina. "
        "Você pode adicionar quantos blocos quiser entre eles."
    )
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
            "name": "delay_between",
            "label": "Pausa entre repetições (segundos)",
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

        try:
            times = int(params.get("times", 3))
            delay = float(params.get("delay_between", 0))
        except ValueError:
            return {"success": False, "message": "Use números para repetições e pausa."}

        if times < 1:
            return {"success": False, "message": "O número de repetições deve ser ≥ 1."}

        return {
            "success": True,
            "message": f"Loop: repetindo {times}x",
            "data": {
                "loop": True,
                "times": times,
                "delay_between": delay,
            }
        }
