import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from blocks.base_block import BaseBlock

# Presets de servidores conhecidos
SMTP_PRESETS = {
    "gmail":   {"host": "smtp.gmail.com",   "port": 587},
    "outlook": {"host": "smtp.office365.com", "port": 587},
    "hotmail": {"host": "smtp.live.com",    "port": 587},
    "yahoo":   {"host": "smtp.mail.yahoo.com", "port": 587},
    "custom":  {"host": "",                 "port": 587},
}


class SendEmailBlock(BaseBlock):
    name = "Enviar E-mail"
    description = "Envia um e-mail via SMTP. Suporta Gmail, Outlook, Yahoo ou servidor personalizado. Aceita texto simples e HTML."
    category = "Integração"

    params_schema = [
        {
            "name": "provider",
            "label": "Provedor (gmail / outlook / yahoo / custom)",
            "type": "str",
            "required": False,
            "default": "gmail",
            "placeholder": "gmail, outlook, yahoo ou custom"
        },
        {
            "name": "smtp_host",
            "label": "Servidor SMTP (só para custom)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: smtp.seudominio.com.br"
        },
        {
            "name": "smtp_port",
            "label": "Porta SMTP (só para custom)",
            "type": "str",
            "required": False,
            "default": "587",
            "placeholder": "587 (TLS) ou 465 (SSL)"
        },
        {
            "name": "sender_email",
            "label": "E-mail remetente",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "seuemail@gmail.com"
        },
        {
            "name": "sender_password",
            "label": "Senha (ou App Password)",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Para Gmail use App Password de 16 dígitos"
        },
        {
            "name": "recipient",
            "label": "Destinatário(s)",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "email@exemplo.com ou vários separados por vírgula"
        },
        {
            "name": "subject",
            "label": "Assunto",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: Relatório PyFlow — {{titulo_pagina}}"
        },
        {
            "name": "body_text",
            "label": "Corpo em texto simples",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Texto do e-mail. Suporta {{variaveis}}"
        },
        {
            "name": "body_html",
            "label": "Corpo em HTML (opcional)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "<h1>Olá!</h1><p>Resultado: {{texto_extraido}}</p>"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        provider       = params.get("provider", "gmail").strip().lower()
        smtp_host_raw  = params.get("smtp_host", "").strip()
        smtp_port_raw  = params.get("smtp_port", "587").strip()
        sender_email   = params.get("sender_email", "").strip()
        sender_password= params.get("sender_password", "").strip()
        recipient_raw  = params.get("recipient", "").strip()
        subject        = params.get("subject", "").strip()
        body_text      = params.get("body_text", "").strip()
        body_html      = params.get("body_html", "").strip()

        # Resolve servidor SMTP
        preset = SMTP_PRESETS.get(provider, SMTP_PRESETS["custom"])
        smtp_host = smtp_host_raw if provider == "custom" else preset["host"]
        try:
            smtp_port = int(smtp_port_raw) if provider == "custom" else preset["port"]
        except ValueError:
            smtp_port = 587

        if not smtp_host:
            return {"success": False, "message": "Servidor SMTP não definido. Preencha 'smtp_host' para provider=custom."}

        # Lista de destinatários
        recipients = [r.strip() for r in recipient_raw.split(",") if r.strip()]
        if not recipients:
            return {"success": False, "message": "Nenhum destinatário válido informado."}

        if not body_text and not body_html:
            return {"success": False, "message": "Informe pelo menos um corpo de e-mail (texto ou HTML)."}

        try:
            # Monta mensagem
            msg = MIMEMultipart("alternative")
            msg["From"]    = sender_email
            msg["To"]      = ", ".join(recipients)
            msg["Subject"] = subject

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))

            # Envia via STARTTLS (porta 587) ou SSL (porta 465)
            context = ssl.create_default_context()

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipients, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipients, msg.as_string())

            return {
                "success": True,
                "message": f"E-mail enviado para {', '.join(recipients)} — Assunto: \"{subject}\""
            }

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "Erro de autenticação. Verifique e-mail e senha.\n💡 Para Gmail: ative a verificação em 2 etapas e gere uma 'App Password' em myaccount.google.com/apppasswords"
            }
        except smtplib.SMTPException as e:
            return {"success": False, "message": f"Erro SMTP: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao enviar e-mail: {str(e)}"}
