from blocks.base_block import BaseBlock

class TimerTriggerBlock(BaseBlock):
    name = "Gatilho: Agendador"
    description = "Define quando este fluxo deve ser executado automaticamente (ex: a cada 5 minutos, todo dia às 08:00)."
    category = "Gatilhos"

    params_schema = [
        {
            "name": "frequency",
            "label": "Frequência",
            "type": "select",
            "required": True,
            "default": "daily",
            "options": [
                {"value": "minutes", "label": "⏱ A cada X minutos"},
                {"value": "hourly",  "label": "🕒 A cada X horas"},
                {"value": "daily",   "label": "📅 Diariamente (hora fixa)"},
                {"value": "weekly",  "label": "🗓 Semanalmente"},
            ]
        },
        {
            "name": "value",
            "label": "Valor (Minutos/Horas ou HH:MM)",
            "type": "str",
            "required": True,
            "default": "08:00",
            "placeholder": "Ex: 5 ou 08:30"
        },
        {
            "name": "active",
            "label": "Ativar Agendamento",
            "type": "bool",
            "required": False,
            "default": True
        }
    ]

    def execute(self, params: dict) -> dict:
        # Blocos de gatilho servem para configuração. 
        # Na execução sequencial, eles apenas confirmam a configuração.
        active = params.get("active", True)
        freq = params.get("frequency", "daily")
        val = params.get("value", "")
        
        status = "ATIVO" if active else "INATIVO"
        return {
            "success": True,
            "message": f"Gatilho de tempo ({status}): {freq} em {val}"
        }
