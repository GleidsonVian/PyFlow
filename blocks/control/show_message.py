from blocks.base_block import BaseBlock
from PySide6.QtCore import QObject, Signal


class _MessageSignaller(QObject):
    """Objeto singleton que emite signal para abrir diálogo na thread principal."""
    show_requested = Signal(str, str, str)  # title, message, kind

_signaller = _MessageSignaller()


class ShowMessageBlock(BaseBlock):
    name = "Exibir Mensagem"
    description = "Exibe uma caixa de diálogo com uma mensagem durante a execução. Útil para debug e exibir valores de variáveis."
    category = "Controle"

    params_schema = [
        {
            "name": "title",
            "label": "Título",
            "type": "str",
            "required": False,
            "default": "PyFlow RPA",
            "placeholder": "Título da janela"
        },
        {
            "name": "message",
            "label": "Mensagem",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: O valor extraído foi: {{minha_variavel}}"
        },
        {
            "name": "kind",
            "label": "Tipo (info / warning / error)",
            "type": "str",
            "required": False,
            "default": "info",
            "placeholder": "info, warning ou error"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        title   = params.get("title", "PyFlow RPA").strip() or "PyFlow RPA"
        message = params.get("message", "").strip()
        kind    = params.get("kind", "info").strip().lower()

        # Emite signal — a MainWindow escuta e abre o diálogo na thread principal
        _signaller.show_requested.emit(title, message, kind)

        return {
            "success": True,
            "message": f"Mensagem exibida: \"{message[:60]}{'...' if len(message) > 60 else ''}\""
        }


def get_signaller() -> _MessageSignaller:
    return _signaller