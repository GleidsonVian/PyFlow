from blocks.base_block import BaseBlock


class CatchBlock(BaseBlock):
    name = "Capturar (Catch)"
    description = (
        "Marca o início do ramo de tratamento de erro dentro de um bloco 'Tentar'. "
        "Os blocos aqui só executam se algo falhar no ramo Tentar. "
        "Use a variável configurada para acessar a mensagem do erro."
    )
    category = "Controle"
    params_schema = [
        {
            "name":        "save_error_to",
            "label":       "Salvar mensagem do erro em variável",
            "type":        "str",
            "required":    False,
            "default":     "erro_capturado",
            "placeholder": "Ex: erro_capturado  →  use {{erro_capturado}} nos blocos seguintes",
        }
    ]

    def execute(self, params: dict) -> dict:
        return {
            "success": True,
            "message": "Capturar — aguardando erros do ramo Tentar",
        }
