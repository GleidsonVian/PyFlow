from blocks.base_block import BaseBlock


class EndWhileBlock(BaseBlock):
    name = "Fim do Enquanto"
    description = "Marca o encerramento do bloco Enquanto (While)."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Enquanto"}
