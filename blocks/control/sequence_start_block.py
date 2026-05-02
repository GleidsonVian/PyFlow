from blocks.base_block import BaseBlock


class SequenceStartBlock(BaseBlock):
    """
    Marca o início de um grupo de blocos que pode ser recolhido na UI.
    """
    name = "Início da Sequência"
    description = "Marca o início de um grupo de blocos que pode ser recolhido para organizar o fluxo."
    category = "Controle"

    params_schema = [
        {
            "name": "sequence_name",
            "label": "Nome da Sequência",
            "type": "str",
            "required": True,
            "default": "Nova Sequência",
            "placeholder": "Ex: Login no Sistema"
        },
    ]

    def execute(self, params: dict) -> dict:
        # Este bloco é puramente para organização da UI e não tem efeito em tempo de execução.
        sequence_name = params.get('sequence_name', 'Sequência')
        return {"success": True, "message": f"Iniciando grupo: {sequence_name}"}