import json
import urllib.request
import urllib.error
from blocks.base_block import BaseBlock
from blocks.browser.extract_text import ExtractTextBlock


class HttpRequestBlock(BaseBlock):
    name = "HTTP Request"
    description = "Faz requisições HTTP (GET, POST, PUT, PATCH, DELETE) para APIs e salva a resposta como variável."
    category = "Integração"

    params_schema = [
        {
            "name": "method",
            "label": "Método",
            "type": "str",
            "required": True,
            "default": "GET",
            "placeholder": "GET, POST, PUT, PATCH ou DELETE"
        },
        {
            "name": "url",
            "label": "URL da API",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "https://api.exemplo.com/endpoint"
        },
        {
            "name": "headers",
            "label": "Headers (JSON — opcional)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": '{"Authorization": "Bearer {{token}}", "Content-Type": "application/json"}'
        },
        {
            "name": "body",
            "label": "Body (JSON — para POST/PUT/PATCH)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": '{"nome": "{{nome}}", "email": "{{email}}"}'
        },
        {
            "name": "json_field",
            "label": "Campo do JSON a extrair (dot notation — opcional)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: data.user.email  ou  results.0.name"
        },
        {
            "name": "variable_name",
            "label": "Salvar resposta como variável",
            "type": "str",
            "required": False,
            "default": "http_resposta",
            "placeholder": "Nome da variável para guardar a resposta"
        },
        {
            "name": "timeout",
            "label": "Timeout (segundos)",
            "type": "str",
            "required": False,
            "default": "15",
            "placeholder": "15"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        method     = params.get("method", "GET").strip().upper()
        url        = params.get("url", "").strip()
        headers_raw = params.get("headers", "").strip()
        body_raw   = params.get("body", "").strip()
        json_field = params.get("json_field", "").strip()
        var_name   = params.get("variable_name", "http_resposta").strip() or "http_resposta"
        try:
            timeout = int(params.get("timeout", 15))
        except ValueError:
            timeout = 15

        if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            return {"success": False, "message": f"Método '{method}' não suportado. Use GET, POST, PUT, PATCH ou DELETE."}

        # Monta headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if headers_raw:
            try:
                headers.update(json.loads(headers_raw))
            except json.JSONDecodeError:
                return {"success": False, "message": "Headers inválidos — deve ser um JSON válido. Ex: {\"Authorization\": \"Bearer token\"}"}

        # Monta body
        body_bytes = None
        if body_raw and method in ("POST", "PUT", "PATCH"):
            try:
                json.loads(body_raw)  # valida JSON
                body_bytes = body_raw.encode("utf-8")
            except json.JSONDecodeError:
                return {"success": False, "message": "Body inválido — deve ser um JSON válido."}

        try:
            req = urllib.request.Request(
                url,
                data=body_bytes,
                headers=headers,
                method=method
            )

            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.status
                raw = response.read().decode("utf-8")

            # Tenta parsear como JSON
            try:
                parsed = json.loads(raw)
                is_json = True
            except json.JSONDecodeError:
                parsed = raw
                is_json = False

            # Extrai campo específico via dot notation
            extracted = None
            if json_field and is_json:
                extracted = self._extract_field(parsed, json_field)
                if extracted is not None:
                    str_val = str(extracted)
                    ExtractTextBlock._context[var_name] = str_val
                    return {
                        "success": True,
                        "message": f"HTTP {method} {status_code} → {var_name}: \"{str_val[:60]}{'...' if len(str_val) > 60 else ''}\"",
                        "data": {"status": status_code, "variable": var_name, "value": extracted}
                    }
                else:
                    return {
                        "success": False,
                        "message": f"HTTP {method} {status_code} OK, mas campo '{json_field}' não encontrado na resposta."
                    }

            # Sem extração: salva resposta completa como string
            value = json.dumps(parsed, ensure_ascii=False) if is_json else raw
            ExtractTextBlock._context[var_name] = value
            preview = value[:80] + ("..." if len(value) > 80 else "")

            return {
                "success": True,
                "message": f"HTTP {method} {status_code} → {var_name}: \"{preview}\"",
                "data": {"status": status_code, "variable": var_name, "value": value}
            }

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return {"success": False, "message": f"HTTP {method} erro {e.code}: {e.reason} — {body[:100]}"}
        except urllib.error.URLError as e:
            return {"success": False, "message": f"Erro de conexão: {str(e.reason)}"}
        except Exception as e:
            return {"success": False, "message": f"Erro na requisição: {str(e)}"}

    def _extract_field(self, data, path: str):
        """
        Extrai campo de um dict/list usando dot notation.
        Ex: 'data.user.email' ou 'results.0.name'
        """
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
            if current is None:
                return None
        return current
