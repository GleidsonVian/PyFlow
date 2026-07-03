"""
Testes do bloco ReadPdfBlock.
Usa mock para simular o pypdf sem precisar de um arquivo .pdf real.
"""
import pytest
from unittest.mock import patch, MagicMock
from blocks.files.read_pdf import ReadPdfBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return ReadPdfBlock()


def _mock_reader(pages_text: list[str]):
    """Cria um mock de PdfReader com N páginas."""
    reader = MagicMock()
    pages = []
    for text in pages_text:
        page = MagicMock()
        page.extract_text.return_value = text
        pages.append(page)
    reader.pages = pages
    return reader


# ── leitura básica ───────────────────────────────────────────────────────────

def _patch_pypdf(mock_reader):
    """
    Cria um mock do módulo pypdf inteiro.
    Necessário porque pypdf pode não estar instalado no ambiente de testes.
    """
    import sys
    import types
    fake_pypdf = types.ModuleType("pypdf")
    fake_pypdf.PdfReader = MagicMock(return_value=mock_reader)
    return patch.dict(sys.modules, {"pypdf": fake_pypdf})


def test_ler_todas_paginas(block):
    mock_reader = _mock_reader(["Página 1 conteúdo", "Página 2 conteúdo"])
    with patch("os.path.exists", return_value=True), _patch_pypdf(mock_reader):
        r = block.execute({
            "filepath": "fake.pdf",
            "pages": "all",
            "page_range": "",
            "variable_name": "pdf_texto",
        })
    assert r["success"] is True
    assert "Página 1" in ctx._context["pdf_texto"]
    assert "Página 2" in ctx._context["pdf_texto"]
    assert ctx._context["pdf_texto_paginas"] == "2"


def test_ler_primeira_pagina(block):
    mock_reader = _mock_reader(["Primeira", "Segunda", "Terceira"])
    with patch("os.path.exists", return_value=True), _patch_pypdf(mock_reader):
        r = block.execute({
            "filepath": "fake.pdf",
            "pages": "first",
            "page_range": "",
            "variable_name": "primeira",
        })
    assert r["success"] is True
    assert ctx._context["primeira"] == "Primeira"


def test_ler_ultima_pagina(block):
    mock_reader = _mock_reader(["A", "B", "Última"])
    with patch("os.path.exists", return_value=True), _patch_pypdf(mock_reader):
        r = block.execute({
            "filepath": "fake.pdf",
            "pages": "last",
            "page_range": "",
            "variable_name": "ultima",
        })
    assert r["success"] is True
    assert ctx._context["ultima"] == "Última"


def test_ler_intervalo(block):
    mock_reader = _mock_reader(["P1", "P2", "P3", "P4"])
    with patch("os.path.exists", return_value=True), _patch_pypdf(mock_reader):
        r = block.execute({
            "filepath": "fake.pdf",
            "pages": "range",
            "page_range": "2-3",
            "variable_name": "trecho",
        })
    assert r["success"] is True
    assert "P2" in ctx._context["trecho"]
    assert "P3" in ctx._context["trecho"]
    assert "P1" not in ctx._context["trecho"]


# ── helper _parse_range ──────────────────────────────────────────────────────

def test_parse_range_hifen():
    assert ReadPdfBlock._parse_range("1-3", 5) == [0, 1, 2]


def test_parse_range_virgula():
    assert ReadPdfBlock._parse_range("1,3,5", 5) == [0, 2, 4]


def test_parse_range_invalido_retorna_todas():
    result = ReadPdfBlock._parse_range("invalido", 3)
    assert result == [0, 1, 2]


# ── erros ────────────────────────────────────────────────────────────────────

def test_arquivo_inexistente(block):
    r = block.execute({
        "filepath": "nao_existe.pdf",
        "pages": "all",
        "page_range": "",
        "variable_name": "r",
    })
    assert r["success"] is False
    assert "não encontrado" in r["message"]


def test_filepath_obrigatorio(block):
    r = block.execute({
        "filepath": "",
        "pages": "all",
        "page_range": "",
        "variable_name": "r",
    })
    assert r["success"] is False
