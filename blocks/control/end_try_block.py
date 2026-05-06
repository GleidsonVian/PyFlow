from blocks.base_block import BaseBlock


class EndTryBlock(BaseBlock):
    name = "Fim do Tentar"
    description = "Marca o encerramento do bloco Tentar/Capturar."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Tentar"}
