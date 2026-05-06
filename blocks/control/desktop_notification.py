from blocks.base_block import BaseBlock


class DesktopNotificationBlock(BaseBlock):
    name = "Notificação Desktop"
    description = "Exibe uma notificação balloon na bandeja do sistema (system tray) sem interromper o fluxo."
    category = "Controle"

    params_schema = [
        {
            "name": "title",
            "label": "Título",
            "type": "str",
            "required": True,
            "default": "PyFlow RPA",
            "placeholder": "Título da notificação"
        },
        {
            "name": "message",
            "label": "Mensagem",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: Fluxo concluído! Resultado: {{texto_extraido}}"
        },
        {
            "name": "duration",
            "label": "Duração (milissegundos)",
            "type": "str",
            "required": False,
            "default": "5000",
            "placeholder": "5000 = 5 segundos"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        title   = params.get("title", "PyFlow RPA").strip() or "PyFlow RPA"
        message = params.get("message", "").strip()
        try:
            duration = int(params.get("duration", 5000))
        except ValueError:
            duration = 5000

        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QApplication
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QTimer

            app = QApplication.instance()
            if not app:
                return {"success": False, "message": "Interface não disponível."}

            def show_tray():
                tray = QSystemTrayIcon(app)
                tray.setIcon(app.style().standardIcon(
                    __import__('PySide6.QtWidgets', fromlist=['QStyle']).QStyle.SP_ComputerIcon
                ))
                tray.show()
                tray.showMessage(title, message, QSystemTrayIcon.Information, duration)
                QTimer.singleShot(duration + 2000, tray.hide)
                QTimer.singleShot(duration + 3000, tray.deleteLater)

            from PySide6.QtCore import Qt
            QTimer.singleShot(0, app, show_tray)

            return {
                "success": True,
                "message": f"Notificação enviada: \"{title} — {message[:50]}{'...' if len(message) > 50 else ''}\""
            }

        except Exception as e:
            return {"success": False, "message": f"Erro ao enviar notificação: {str(e)}"}