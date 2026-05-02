"""
Bloco de requisição HTTP do PyFlow RPA.
Usa a biblioteca requests para GET/POST/PUT/PATCH/DELETE.
Coloque em: blocks/integration/http_request.py
"""
import json
import requests
from blocks.base_block import BaseBlock


class HttpRequestBlock(BaseBlock):
    name        = "HTTP Request"
    description = "Realiza requisições HTTP para APIs REST usando a biblioteca requests. Suporta GET, POST, PUT, PATCH e DELETE com headers, body e extração de campos JSON via dot notation."
    category    = "Integração"

    params_schema = [
        {
            "name":        "method",
            "label":       "Método HTTP",
            "type":        "str",
            "required":    True,
            "default":     "GET",
            "placeholder": "GET | POST | PUT | PATCH | DELETE"
        },
        {
            "name":        "url",
            "label":       "URL",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "https://api.exemplo.com/endpoint"
        },
        {
            "name":        "headers",
            "label":       "Headers (JSON)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": '{"Authorization": "Bearer {{token}}", "Content-Type": "application/json"}'
        },
        {
            "name":        "body",
            "label":       "Body (JSON — para POST/PUT/PATCH)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": '{"nome": "{{nome}}", "valor": "{{valor}}"}'
        },
        {
            "name":        "json_field",
            "label":       "Campo do JSON a extrair (dot notation)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: data.user.email | results.0.name | total"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar resposta como variável",
            "type":        "str",
            "required":    False,
            "default":     "http_resposta",
            "placeholder": "Nome da variável onde salvar a resposta ou campo extraído"
        },
        {
            "name":        "timeout",
            "label":       "Timeout (segundos)",
            "type":        "str",
            "required":    False,
            "default":     "15",
            "placeholder": "15"
        },
        {
            "name":        "verify_ssl",
            "label":       "Verificar SSL",
            "type":        "bool",
            "required":    False,
            "default":     True
        },
    ]

    METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        method     = params.get("method", "GET").strip().upper()
        url        = params.get("url", "").strip()
        json_field = params.get("json_field", "").strip()
        var_name   = params.get("variable_name", "http_resposta").strip() or "http_resposta"
        verify_ssl = params.get("verify_ssl", True)

        try:
            timeout = float(params.get("timeout", 15))
        except ValueError:
            timeout = 15.0

        if method not in self.METHODS:
            return {"success": False, "message": f"Método '{method}' inválido. Use: {', '.join(sorted(self.METHODS))}"}

        headers = self._parse_json(params.get("headers", ""), "headers")
        if isinstance(headers, str):
            return {"success": False, "message": headers}

        body = self._parse_json(params.get("body", ""), "body")
        if isinstance(body, str):
            return {"success": False, "message": body}

        try:
            response = requests.request(
                method  = method,
                url     = url,
                headers = headers or None,
                json    = body or None,
                timeout = timeout,
                verify  = verify_ssl,
            )

            status = response.status_code

            try:
                data = response.json()
            except Exception:
                data = response.text

            extracted = self._extract_field(data, json_field) if json_field else data

            from blocks.browser.extract_text import ExtractTextBlock
            context = ExtractTextBlock._context
            context[var_name]             = extracted
            context[f"{var_name}_status"] = str(status)
            context[f"{var_name}_ok"]     = str(response.ok)

            preview = str(extracted)[:80] + ("..." if len(str(extracted)) > 80 else "")

            if not response.ok:
                return {"success": False, "message": f"HTTP {status} {response.reason}: {str(data)[:200]}"}

            return {
                "success": True,
                "message": f"HTTP {method} {status} → '{var_name}': {preview}",
                "data":    {"response": extracted, "status": status}
            }

        except requests.exceptions.Timeout:
            return {"success": False, "message": f"Timeout após {timeout}s — {url}"}
        except requests.exceptions.SSLError as e:
            return {"success": False, "message": f"Erro SSL: {str(e)[:200]}. Desative 'Verificar SSL' se necessário."}
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "message": f"Erro de conexão: {str(e)[:200]}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Erro na requisição: {str(e)[:200]}"}

    def _parse_json(self, raw: str, field_name: str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            return f"JSON inválido no campo '{field_name}': {str(e)}"

    def _extract_field(self, data, dot_path: str):
        current = data
        for key in dot_path.split("."):
            if current is None:
                return ""
            if isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return ""
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                return str(current)
        return current if current is not None else ""