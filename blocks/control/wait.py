import time

from blocks.base_block import BaseBlock


class WaitBlock(BaseBlock):
    name = "Aguardar"
    description = "Pausa a execução por um número determinado de segundos"
    category = "Controle"

    params_schema = [
        {
            "name": "seconds",
            "label": "Segundos",
            "type": "str",
            "required": True,
            "default": "3",
            "placeholder": "Ex: 3"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        try:
            seconds = float(params.get("seconds", 3))
        except ValueError:
            return {"success": False, "message": "Valor de segundos inválido. Use um número (ex: 3 ou 1.5)."}

        if seconds < 0:
            return {"success": False, "message": "O tempo de espera não pode ser negativo."}

        time.sleep(seconds)
        return {
            "success": True,
            "message": f"Aguardou {seconds} segundo(s)"
        }