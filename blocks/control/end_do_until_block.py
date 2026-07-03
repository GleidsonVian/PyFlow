from blocks.base_block import BaseBlock


class EndDoUntilBlock(BaseBlock):
    name = "Fim do Repetir Até"
    description = "Marca o fim do bloco 'Repetir Até (Do Until)'."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Repetir Até"}
