from blocks.base_block import BaseBlock


class EndLoopBlock(BaseBlock):
    name = "Fim do Loop"
    description = "Marca o fim do escopo do bloco 'Loop (Repetir)'. Coloque após o último bloco que deve ser repetido."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Loop"}
