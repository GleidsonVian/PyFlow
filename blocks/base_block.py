from abc import ABC, abstractmethod


class BaseBlock(ABC):
    """
    Classe abstrata que todo bloco do PyFlow deve herdar.
    Cada bloco representa uma ação automatizada.
    """

    # Nome exibido na interface (painel de blocos)
    name: str = "Bloco sem nome"

    # Descrição curta exibida na interface
    description: str = ""

    # Categoria para agrupar blocos no painel
    category: str = "Geral"

    # Lista de parâmetros que o bloco aceita
    # Formato: [{"name": "url", "label": "URL", "type": "str", "required": True, "default": ""}]
    params_schema: list = []

    @abstractmethod
    def execute(self, params: dict) -> dict:
        """
        Executa a ação do bloco.

        Args:
            params: dicionário com os parâmetros preenchidos pelo usuário

        Returns:
            dict com:
                - "success": bool indicando se executou com sucesso
                - "message": mensagem de resultado ou erro
                - "data": dados extras (opcional)
        """
        pass

    def validate_params(self, params: dict) -> list[str]:
        """
        Valida os parâmetros antes de executar.
        Retorna lista de erros (vazia = tudo ok).
        """
        errors = []
        for schema in self.params_schema:
            if schema.get("required") and not params.get(schema["name"]):
                errors.append(f"O campo '{schema['label']}' é obrigatório.")
        return errors

    def __repr__(self):
        return f"<Block: {self.name}>"