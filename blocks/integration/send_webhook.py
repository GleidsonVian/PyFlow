"""
Bloco de envio para Webhook externo do PyFlow RPA.
Faz POST para qualquer URL de webhook (Zapier, Make, n8n, etc.)
com payload JSON configurável via template {{variavel}}.
Coloque em: blocks/integration/send_webhook.py
"""
import json
import requests
from blocks.base_block import BaseBlock


class SendWebhookBlock(BaseBlock):
    name        = "Enviar para Webhook"
    description = (
        "Envia um POST JSON para qualquer URL de webhook externo: "
        "Zapier, Make (Integromat), n8n, Discord, Slack, ou URL própria. "
        "O payload é configurável com variáveis {{nome}}."
    )
    category = "Integração"

    params_schema = [
        {
            "name":    "url",
            "label":   "URL do Webhook",
            "type":    "str",
            "required": True,
            "default": "",
            "placeholder": "https://hooks.zapier.com/hooks/catch/... ou https://hook.eu1.make.com/..."
        },
        {
            "name":    "payload",
            "label":   "Payload JSON (aceita {{variavel}})",
            "type":    "str",
            "required": False,
            "default": '{"mensagem": "{{mensagem}}", "status": "ok"}',
            "placeholder": '{"campo": "{{variavel}}", "fixo": "valor"}'
        },
        {
            "name":    "headers",
            "label":   "Headers extras (JSON opcional)",
            "type":    "str",
            "required": False,
            "default": "",
            "placeholder": '{"Authorization": "Bearer {{token}}"}'
        },
        {
            "name":    "variable_name",
            "label":   "Salvar resposta como variável (opcional)",
            "type":    "str",
            "required": False,
            "default": "webhook_resposta",
            "placeholder": "Nome da variável para salvar a resposta do servidor"
        },
        {
            "name":    "timeout",
            "label":   "Timeout (segundos)",
            "type":    "str",
            "required": False,
            "default": "15",
            "placeholder": "15"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        url      = params.get("url", "").strip()
        payload  = params.get("payload", "").strip()
        headers  = params.get("headers", "").strip()
        var_name = params.get("variable_name", "webhook_resposta").strip() or "webhook_resposta"

        try:
            timeout = float(params.get("timeout", 15))
        except ValueError:
            timeout = 15.0

        if not url:
            return {"success": False, "message": "URL do Webhook é obrigatória."}

        # Parseia payload JSON
        body = None
        if payload:
            try:
                body = json.loads(payload)
            except json.JSONDecodeError as e:
                return {"success": False, "message": f"Payload JSON inválido: {str(e)}"}

        # Parseia headers JSON
        extra_headers = {"Content-Type": "application/json"}
        if headers:
            try:
                extra_headers.update(json.loads(headers))
            except json.JSONDecodeError as e:
                return {"success": False, "message": f"Headers JSON inválido: {str(e)}"}

        try:
            response = requests.post(
                url,
                json=body,
                headers=extra_headers,
                timeout=timeout,
            )

            status = response.status_code

            # Tenta interpretar a resposta como JSON
            try:
                resp_data = response.json()
            except Exception:
                resp_data = response.text

            # Salva resposta no contexto
            if var_name:
                from blocks.browser.extract_text import ExtractTextBlock
                ExtractTextBlock._context[var_name] = resp_data
                ExtractTextBlock._context[f"{var_name}_status"] = str(status)

            preview = str(resp_data)[:80] + ("..." if len(str(resp_data)) > 80 else "")

            if not response.ok:
                return {
                    "success": False,
                    "message": f"Webhook respondeu HTTP {status}: {str(resp_data)[:200]}"
                }

            return {
                "success": True,
                "message": f"Webhook enviado! HTTP {status} → '{var_name}': {preview}",
                "data":    {"response": resp_data, "status": status}
            }

        except requests.exceptions.Timeout:
            return {"success": False, "message": f"Timeout após {timeout}s — {url}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": f"Erro de conexão — verifique a URL: {url}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Erro ao enviar webhook: {str(e)[:200]}"}
