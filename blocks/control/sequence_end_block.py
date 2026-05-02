from blocks.base_block import BaseBlock


class SequenceEndBlock(BaseBlock):
    """
    Marca o fim de um grupo de blocos que pode ser recolhido na UI.
    """
    name = "Fim da Sequência"
    description = "Marca o fim de um grupo de blocos que pode ser recolhido."
    category = "Controle"

    params_schema = []

    def execute(self, params: dict) -> dict:
        # Este bloco é puramente para organização da UI e não tem efeito em tempo de execução.
        return {"success": True, "message": "Finalizando grupo."}