from blocks.base_block import BaseBlock


class ReadPdfBlock(BaseBlock):
    name        = "Ler PDF"
    description = "Extrai texto de um arquivo PDF e salva em variável. Suporta PDFs de texto (não scaneados)."
    category    = "Arquivos"

    params_schema = [
        {
            "name":        "filepath",
            "label":       "Caminho do arquivo PDF",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: documentos/nota_fiscal.pdf",
        },
        {
            "name":    "pages",
            "label":   "Páginas a extrair",
            "type":    "select",
            "required": True,
            "default": "all",
            "options": [
                {"value": "all",   "label": "Todas as páginas"},
                {"value": "first", "label": "Só a primeira página"},
                {"value": "last",  "label": "Só a última página"},
                {"value": "range", "label": "Intervalo específico"},
            ],
        },
        {
            "name":        "page_range",
            "label":       "Intervalo de páginas (ex: 1-3 ou 2,4,6)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "1-3  ou  1,2,5  (somente se Páginas = Intervalo)",
        },
        {
            "name":        "variable_name",
            "label":       "Salvar texto na variável",
            "type":        "str",
            "required":    False,
            "default":     "pdf_texto",
            "placeholder": "Nome da variável",
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        import os
        filepath = params.get("filepath", "").strip()
        pages    = params.get("pages", "all")
        rng      = params.get("page_range", "").strip()
        var_name = params.get("variable_name", "pdf_texto").strip() or "pdf_texto"

        if not os.path.exists(filepath):
            return {"success": False, "message": f"Arquivo não encontrado: {filepath}"}

        try:
            from pypdf import PdfReader
        except ImportError:
            return {"success": False, "message": "pypdf não instalado. Execute: pip install pypdf"}

        try:
            reader   = PdfReader(filepath)
            n_pages  = len(reader.pages)

            if pages == "all":
                indices = list(range(n_pages))
            elif pages == "first":
                indices = [0]
            elif pages == "last":
                indices = [n_pages - 1]
            elif pages == "range":
                indices = self._parse_range(rng, n_pages)
            else:
                indices = list(range(n_pages))

            text_parts = []
            for i in indices:
                if 0 <= i < n_pages:
                    t = reader.pages[i].extract_text() or ""
                    if t.strip():
                        text_parts.append(t)

            full_text = "\n\n".join(text_parts).strip()

            from blocks.browser.extract_text import ExtractTextBlock
            ExtractTextBlock._context[var_name] = full_text
            ExtractTextBlock._context[f"{var_name}_paginas"] = str(n_pages)

            preview = full_text[:120].replace("\n", " ")
            return {
                "success": True,
                "message": f"PDF lido: {n_pages} página(s), {len(full_text)} chars → '{var_name}'",
                "data": {
                    "variable":    var_name,
                    "pages_total": n_pages,
                    "chars":       len(full_text),
                    "preview":     preview,
                },
            }

        except Exception as e:
            return {"success": False, "message": f"Erro ao ler PDF: {e}"}

    @staticmethod
    def _parse_range(rng: str, n_pages: int) -> list:
        indices = []
        for part in rng.replace(" ", "").split(","):
            if "-" in part:
                a, _, b = part.partition("-")
                try:
                    for i in range(int(a) - 1, int(b)):
                        indices.append(i)
                except ValueError:
                    pass
            elif part.isdigit():
                indices.append(int(part) - 1)
        return indices or list(range(n_pages))
