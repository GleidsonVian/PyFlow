from blocks.base_block import BaseBlock


class EndForEachBlock(BaseBlock):
    name = "Fim do Para Cada"
    description = "Marca o fim do escopo do bloco 'Para Cada (For Each)'. Coloque após o último bloco que deve ser iterado."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Para Cada"}
