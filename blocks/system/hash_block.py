"""
Bloco de Hash / Criptografia do PyFlow RPA.
MD5, SHA1, SHA256, SHA512, base64 encode/decode, URL encode/decode.
Coloque em: blocks/system/hash_block.py

Sem dependências externas — usa hashlib, base64 e urllib da stdlib.
"""
import hashlib
import base64
import hmac
from urllib.parse import quote, unquote
from blocks.base_block import BaseBlock


class HashBlock(BaseBlock):
    name        = "Hash / Criptografia"
    description = "Gera hashes (MD5, SHA256, SHA512), codifica/decodifica Base64, URL encode/decode e gera HMAC. Usa biblioteca padrão do Python — sem instalar nada."
    category    = "Sistema"

    params_schema = [
        {
            "name":        "operation",
            "label":       "Operação",
            "type":        "str",
            "required":    True,
            "default":     "sha256",
            "placeholder": "md5 | sha1 | sha256 | sha512 | base64_encode | base64_decode | url_encode | url_decode | hmac_sha256"
        },
        {
            "name":        "input_value",
            "label":       "Valor de entrada",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Texto ou {{variavel}} a processar"
        },
        {
            "name":        "secret_key",
            "label":       "Chave secreta (somente hmac_sha256)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Chave HMAC. Aceita {{ASSET:CHAVE_HMAC}}"
        },
        {
            "name":        "encoding",
            "label":       "Encoding do texto",
            "type":        "str",
            "required":    False,
            "default":     "utf-8",
            "placeholder": "utf-8 | latin-1 | ascii"
        },
        {
            "name":        "uppercase",
            "label":       "Hash em maiúsculas",
            "type":        "bool",
            "required":    False,
            "default":     False
        },
        {
            "name":        "variable_name",
            "label":       "Salvar resultado como variável",
            "type":        "str",
            "required":    False,
            "default":     "hash_resultado",
            "placeholder": "Nome da variável para o resultado"
        },
    ]

    OPERATIONS = {
        "md5", "sha1", "sha256", "sha512",
        "base64_encode", "base64_decode",
        "url_encode", "url_decode",
        "hmac_sha256",
    }

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        operation   = params.get("operation", "sha256").strip().lower()
        input_value = params.get("input_value", "")
        secret_key  = params.get("secret_key", "").strip()
        encoding    = params.get("encoding", "utf-8").strip() or "utf-8"
        uppercase   = params.get("uppercase", False)
        var_name    = params.get("variable_name", "hash_resultado").strip() or "hash_resultado"

        if operation not in self.OPERATIONS:
            valid = " | ".join(sorted(self.OPERATIONS))
            return {"success": False, "message": f"Operação '{operation}' inválida.\nUse: {valid}"}

        if not input_value and operation not in {"base64_decode", "url_decode"}:
            return {"success": False, "message": "input_value é obrigatório."}

        try:
            result = self._run(operation, input_value, secret_key, encoding, uppercase)
        except LookupError:
            return {"success": False, "message": f"Encoding '{encoding}' inválido. Use: utf-8, latin-1, ascii"}
        except Exception as e:
            return {"success": False, "message": f"Erro na operação '{operation}': {str(e)}"}

        from blocks.browser.extract_text import ExtractTextBlock
        ExtractTextBlock._context[var_name] = result

        preview = str(result)[:60] + ("..." if len(str(result)) > 60 else "")
        return {
            "success": True,
            "message": f"{operation} → '{var_name}': {preview}",
            "data":    {"result": result, "operation": operation}
        }

    def _run(self, operation: str, value: str, key: str, encoding: str, uppercase: bool) -> str:

        # ── Hashes ────────────────────────────────────────────────────
        if operation in {"md5", "sha1", "sha256", "sha512"}:
            algo   = hashlib.new(operation if operation != "md5" else "md5")
            algo   = getattr(hashlib, operation)(value.encode(encoding))
            result = algo.hexdigest()
            return result.upper() if uppercase else result

        # ── HMAC ──────────────────────────────────────────────────────
        if operation == "hmac_sha256":
            if not key:
                raise ValueError("secret_key é obrigatório para hmac_sha256.")
            h = hmac.new(key.encode(encoding), value.encode(encoding), hashlib.sha256)
            result = h.hexdigest()
            return result.upper() if uppercase else result

        # ── Base64 ────────────────────────────────────────────────────
        if operation == "base64_encode":
            encoded = base64.b64encode(value.encode(encoding))
            return encoded.decode("ascii")

        if operation == "base64_decode":
            # Adiciona padding se necessário
            padded = value + "=" * (-len(value) % 4)
            decoded = base64.b64decode(padded)
            return decoded.decode(encoding)

        # ── URL encode/decode ─────────────────────────────────────────
        if operation == "url_encode":
            return quote(value, safe="")

        if operation == "url_decode":
            return unquote(value)

        raise ValueError(f"Operação não implementada: {operation}")
