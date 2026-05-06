from blocks.base_block import BaseBlock


class EndIfBlock(BaseBlock):
    name = "Fim do Se"
    description = "Marca o fim do escopo do bloco 'Condição (Se)'. Obrigatório após o bloco Se (e após o Senão, se usado)."
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {"success": True, "message": "Fim do Se"}
