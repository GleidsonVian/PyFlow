import os
import shutil
from blocks.base_block import BaseBlock

class FileManagerBlock(BaseBlock):
    name = "Gerenciar Arquivos"
    description = "Realiza operações de sistema de arquivos como mover, copiar, renomear ou deletar arquivos e pastas."
    category = "Arquivos"

    params_schema = [
        {
            "name": "action",
            "label": "Operação",
            "type": "select",
            "required": True,
            "default": "move",
            "options": [
                {"value": "move",   "label": "📦 Mover",   "description": "Move o arquivo/pasta da origem para o destino."},
                {"value": "copy",   "label": "📋 Copiar",  "description": "Copia o arquivo/pasta da origem para o destino."},
                {"value": "rename", "label": "✏️ Renomear", "description": "Altera o nome do arquivo/pasta (mesmo que mover se o caminho for o mesmo)."},
                {"value": "delete", "label": "🗑 Deletar",  "description": "Remove permanentemente o arquivo ou a pasta (e todo seu conteúdo)."},
                {"value": "exists", "label": "🔍 Verificar Existência", "description": "Verifica se o arquivo/pasta existe e salva True/False em uma variável."},
            ]
        },
        {
            "name": "source",
            "label": "Caminho de Origem",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: arquivos/relatorio.pdf"
        },
        {
            "name": "destination",
            "label": "Caminho de Destino (Ignorado para Deletar/Verificar)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "Ex: backup/relatorio_final.pdf"
        },
        {
            "name": "variable_name",
            "label": "Salvar resultado em (Opcional)",
            "type": "str",
            "required": False,
            "default": "file_result",
            "placeholder": "Nome da variável para salvar True/False ou o novo caminho"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        action      = params.get("action", "move").strip().lower()
        source      = params.get("source", "").strip()
        destination = params.get("destination", "").strip()
        var_name    = params.get("variable_name", "file_result").strip() or "file_result"

        if not source:
            return {"success": False, "message": "O caminho de origem é obrigatório."}

        try:
            # Contexto para salvar variáveis
            from blocks.browser.extract_text import ExtractTextBlock
            context = ExtractTextBlock._context

            if action == "exists":
                exists = os.path.exists(source)
                context[var_name] = exists
                return {
                    "success": True,
                    "message": f"Verificação: '{source}' {'existe' if exists else 'não existe'}.",
                    "data": {"exists": exists}
                }

            if not os.path.exists(source):
                return {"success": False, "message": f"Origem não encontrada: {source}"}

            if action == "delete":
                if os.path.isdir(source):
                    shutil.rmtree(source)
                    msg = f"Pasta deletada: {source}"
                else:
                    os.remove(source)
                    msg = f"Arquivo deletado: {source}"
                return {"success": True, "message": msg}

            if not destination:
                return {"success": False, "message": f"O caminho de destino é obrigatório para a operação '{action}'."}

            # Garante que a pasta de destino exista
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            if action == "move" or action == "rename":
                shutil.move(source, destination)
                context[var_name] = destination
                return {"success": True, "message": f"Movido/Renomeado: {source} → {destination}"}

            if action == "copy":
                if os.path.isdir(source):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    msg = f"Pasta copiada: {source} → {destination}"
                else:
                    shutil.copy2(source, destination)
                    msg = f"Arquivo copiado: {source} → {destination}"
                context[var_name] = destination
                return {"success": True, "message": msg}

        except Exception as e:
            return {"success": False, "message": f"Erro na operação '{action}': {str(e)}"}

        return {"success": False, "message": f"Operação '{action}' desconhecida."}
