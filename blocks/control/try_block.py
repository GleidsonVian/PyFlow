from blocks.base_block import BaseBlock


class TryBlock(BaseBlock):
    name = "Tentar (Try)"
    description = (
        "Executa os blocos internos e, se qualquer um falhar, "
        "desvia para o ramo 'Capturar' em vez de parar o fluxo. "
        "Sempre finalize com 'Fim do Tentar'."
    )
    category = "Controle"
    params_schema = []

    def execute(self, params: dict) -> dict:
        return {
            "success": True,
            "message": "Tentando executar bloco(s)...",
            "data": {"try": True},
        }
