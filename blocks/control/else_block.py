from blocks.base_block import BaseBlock


class ElseBlock(BaseBlock):
    name = "Senão (Else)"
    description = "Marca o início do ramo alternativo dentro de um bloco 'Condição (Se)'. Os blocos entre Senão e Fim do Se rodam quando a condição for falsa."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Senão"}
