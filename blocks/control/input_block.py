from blocks.base_block import BaseBlock
from PySide6.QtCore import QObject, Signal
import engine.execution_context as ctx
import threading

class SyncResult:
    """Objeto simples para carregar dados entre threads sem ser copiado."""
    def __init__(self):
        self.text = None
        self.event = threading.Event()

class _InputSignaller(QObject):
    """Signaller para solicitar input da thread principal."""
    # Passamos o objeto de resultado que contém o evento e o campo de texto
    input_requested = Signal(str, str, str, object)

_input_signaller = _InputSignaller()

class InputBlock(BaseBlock):
    name = "Solicitar Entrada"
    description = "Abre uma caixa de diálogo e aguarda o usuário digitar um valor. O resultado é salvo em uma variável."
    category = "Controle"

    params_schema = [
        {
            "name": "variable_name",
            "label": "Salvar na Variável",
            "type": "str",
            "required": True,
            "default": "input_usuario"
        },
        {
            "name": "label",
            "label": "Texto da Pergunta",
            "type": "str",
            "required": True,
            "default": "Digite o valor:"
        },
        {
            "name": "title",
            "label": "Título da Janela",
            "type": "str",
            "required": False,
            "default": "Entrada de Dados"
        },
        {
            "name": "default_value",
            "label": "Valor Padrão",
            "type": "str",
            "required": False,
            "default": ""
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        var_name = params.get("variable_name", "input_usuario").strip()
        label    = params.get("label", "Digite o valor:")
        title    = params.get("title", "Entrada de Dados")
        default  = params.get("default_value", "")

        # Cria o objeto de sincronização
        result = SyncResult()

        # Emite o sinal passando o OBJETO (referência direta)
        _input_signaller.input_requested.emit(title, label, default, result)

        # Aguarda o sinal da UI (máximo 10 min)
        if not result.event.wait(timeout=600):
            return {"success": False, "message": "Timeout aguardando resposta."}

        if result.text is not None:
            ctx.get()[var_name] = result.text
            return {
                "success": True, 
                "message": f"Valor '{result.text}' salvo em '{{{{{var_name}}}}}'"
            }
        else:
            return {"success": False, "message": "Entrada cancelada pelo usuário."}

def get_input_signaller() -> _InputSignaller:
    return _input_signaller
