import os
from blocks.base_block import BaseBlock

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class ReadPdfBlock(BaseBlock):
    name = "Ler PDF"
    description = "Extrai o texto de um arquivo PDF e salva em uma variável."
    category = "Arquivos"

    params_schema = [
        {
            "name": "file_path",
            "label": "Caminho do arquivo PDF",
            "type": "str",
            "required": True,
            "default": "",
            "placeholder": "Ex: documentos/livro.pdf"
        },
        {
            "name": "variable_name",
            "label": "Salvar texto em",
            "type": "str",
            "required": False,
            "default": "texto_pdf",
            "placeholder": "Nome da variável"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        if pdfplumber is None:
            return {"success": False, "message": "Biblioteca 'pdfplumber' não instalada. Reinicie o PyFlow para instalar automaticamente."}

        file_path = params.get("file_path", "").strip()
        var_name = params.get("variable_name", "texto_pdf").strip() or "texto_pdf"
        
        if not os.path.exists(file_path):
            return {"success": False, "message": f"Arquivo não encontrado: {file_path}"}

        try:
            full_text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
            
            final_text = "\n".join(full_text)
            
            # Salva no contexto central
            import engine.execution_context as ctx
            ctx.get()[var_name] = final_text
            
            return {
                "success": True,
                "message": f"PDF lido com sucesso. Páginas: {len(pdf.pages)}. Caracteres: {len(final_text)}",
                "data": {"text": final_text, "pages_count": len(pdf.pages)}
            }
        except Exception as e:
            return {"success": False, "message": f"Erro ao ler PDF: {str(e)}"}
