"""
Bloco ZIP do PyFlow RPA.
Compacta e descompacta arquivos usando zipfile nativo do Python.
Coloque em: blocks/files/zip_block.py

Sem dependências externas — usa zipfile da biblioteca padrão do Python.
"""
import os
import zipfile
from blocks.base_block import BaseBlock


class ZipBlock(BaseBlock):
    name        = "ZIP (Compactar / Descompactar)"
    description = "Compacta arquivos/pastas em .zip ou descompacta um .zip existente. Usa zipfile nativo do Python — sem instalar nada."
    category    = "Arquivos"

    params_schema = [
        {
            "name":        "action",
            "label":       "Ação",
            "type":        "str",
            "required":    True,
            "default":     "compress",
            "placeholder": "compress = compactar | extract = descompactar | list = listar conteúdo | add = adicionar arquivo"
        },
        {
            "name":        "zip_path",
            "label":       "Caminho do arquivo .zip",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: saida/relatorio.zip | backup.zip"
        },
        {
            "name":        "source_path",
            "label":       "Arquivo ou pasta a compactar (compress / add)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: saida/ | relatorio.csv | screenshots/ — aceita {{variavel}}"
        },
        {
            "name":        "extract_to",
            "label":       "Pasta de destino (extract)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: downloads/ | extraido/ — vazio = mesma pasta do .zip"
        },
        {
            "name":        "compression",
            "label":       "Nível de compressão (compress)",
            "type":        "str",
            "required":    False,
            "default":     "deflated",
            "placeholder": "deflated = padrão | stored = sem compressão | bzip2 | lzma"
        },
        {
            "name":        "password",
            "label":       "Senha do ZIP (somente extract)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Senha para descompactar ZIP protegido"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar lista de arquivos como variável (list)",
            "type":        "str",
            "required":    False,
            "default":     "zip_lista",
            "placeholder": "Nome da variável para salvar conteúdo do ZIP"
        },
    ]

    COMPRESSIONS = {
        "deflated": zipfile.ZIP_DEFLATED,
        "stored":   zipfile.ZIP_STORED,
        "bzip2":    zipfile.ZIP_BZIP2,
        "lzma":     zipfile.ZIP_LZMA,
    }
    ACTIONS = {"compress", "extract", "list", "add"}

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        action      = params.get("action", "compress").strip().lower()
        zip_path    = params.get("zip_path", "").strip()
        source_path = params.get("source_path", "").strip()
        extract_to  = params.get("extract_to", "").strip()
        compression = params.get("compression", "deflated").strip().lower()
        password    = params.get("password", "").strip()
        var_name    = params.get("variable_name", "zip_lista").strip() or "zip_lista"

        if action not in self.ACTIONS:
            return {"success": False, "message": f"Ação '{action}' inválida. Use: {', '.join(sorted(self.ACTIONS))}"}
        if not zip_path:
            return {"success": False, "message": "zip_path é obrigatório."}

        compress_mode = self.COMPRESSIONS.get(compression, zipfile.ZIP_DEFLATED)

        try:
            if action == "compress":
                return self._compress(zip_path, source_path, compress_mode)
            if action == "extract":
                return self._extract(zip_path, extract_to, password)
            if action == "list":
                return self._list(zip_path, var_name)
            if action == "add":
                return self._add(zip_path, source_path, compress_mode)
        except zipfile.BadZipFile:
            return {"success": False, "message": f"Arquivo inválido ou corrompido: {zip_path}"}
        except Exception as e:
            return {"success": False, "message": f"Erro no ZIP: {str(e)}"}

    # ── Compactar ─────────────────────────────────────────────────────

    def _compress(self, zip_path: str, source_path: str, compression: int) -> dict:
        if not source_path:
            return {"success": False, "message": "source_path é obrigatório para compress."}
        if not os.path.exists(source_path):
            return {"success": False, "message": f"Caminho não encontrado: {source_path}"}

        os.makedirs(os.path.dirname(zip_path) or ".", exist_ok=True)
        file_count = 0

        with zipfile.ZipFile(zip_path, "w", compression=compression) as zf:
            if os.path.isfile(source_path):
                zf.write(source_path, os.path.basename(source_path))
                file_count = 1
            else:
                for root, _, files in os.walk(source_path):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arc_name = os.path.relpath(abs_path, os.path.dirname(source_path))
                        zf.write(abs_path, arc_name)
                        file_count += 1

        size = os.path.getsize(zip_path)
        return {
            "success": True,
            "message": f"Compactado: {file_count} arquivo(s) → {zip_path} ({size:,} bytes)"
        }

    # ── Descompactar ──────────────────────────────────────────────────

    def _extract(self, zip_path: str, extract_to: str, password: str) -> dict:
        if not os.path.exists(zip_path):
            return {"success": False, "message": f"Arquivo não encontrado: {zip_path}"}

        dest = extract_to or os.path.dirname(zip_path) or "."
        os.makedirs(dest, exist_ok=True)

        pwd = password.encode() if password else None

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest, pwd=pwd)
            count = len(zf.namelist())

        return {
            "success": True,
            "message": f"Extraído: {count} arquivo(s) de {zip_path} → {dest}"
        }

    # ── Listar conteúdo ───────────────────────────────────────────────

    def _list(self, zip_path: str, var_name: str) -> dict:
        if not os.path.exists(zip_path):
            return {"success": False, "message": f"Arquivo não encontrado: {zip_path}"}

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            infos = [
                {
                    "nome":     info.filename,
                    "tamanho":  info.file_size,
                    "comprimido": info.compress_size,
                }
                for info in zf.infolist()
            ]

        from blocks.browser.extract_text import ExtractTextBlock
        ctx = ExtractTextBlock._context
        ctx[var_name]            = names
        ctx[f"{var_name}_total"] = str(len(names))
        ctx[f"{var_name}_info"]  = infos

        preview = ", ".join(names[:5]) + ("..." if len(names) > 5 else "")
        return {
            "success": True,
            "message": f"ZIP contém {len(names)} arquivo(s) → '{var_name}': {preview}"
        }

    # ── Adicionar arquivo a ZIP existente ─────────────────────────────

    def _add(self, zip_path: str, source_path: str, compression: int) -> dict:
        if not source_path:
            return {"success": False, "message": "source_path é obrigatório para add."}
        if not os.path.exists(source_path):
            return {"success": False, "message": f"Arquivo não encontrado: {source_path}"}

        os.makedirs(os.path.dirname(zip_path) or ".", exist_ok=True)
        mode = "a" if os.path.exists(zip_path) else "w"

        with zipfile.ZipFile(zip_path, mode, compression=compression) as zf:
            if os.path.isfile(source_path):
                zf.write(source_path, os.path.basename(source_path))
                added = 1
            else:
                added = 0
                for root, _, files in os.walk(source_path):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arc_name = os.path.relpath(abs_path, os.path.dirname(source_path))
                        zf.write(abs_path, arc_name)
                        added += 1

        return {
            "success": True,
            "message": f"Adicionado {added} arquivo(s) em {zip_path}"
        }
