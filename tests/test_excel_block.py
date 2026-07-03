"""
Testes do bloco ExcelBlock.
Usa um arquivo temporário criado e deletado em cada teste.
Requer: pip install openpyxl
"""
import os
import pytest

TMP_FILE = "tests/_tmp_test.xlsx"


@pytest.fixture(autouse=True)
def cleanup_xlsx():
    """Remove o arquivo temporário antes e depois de cada teste."""
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)
    yield
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)


@pytest.fixture
def block():
    from blocks.files.excel_block import ExcelBlock
    return ExcelBlock()


@pytest.fixture
def arquivo_com_dados(block):
    """Cria um xlsx com dados de exemplo e retorna o caminho."""
    block.execute({"action": "create", "filepath": TMP_FILE,
                   "sheet": "", "cell": "", "column": "", "row": "",
                   "value": "", "skip_header": True, "variable_name": "r"})
    block.execute({"action": "write_cell", "filepath": TMP_FILE,
                   "sheet": "", "cell": "A1", "column": "", "row": "",
                   "value": "Nome", "skip_header": True, "variable_name": "r"})
    block.execute({"action": "write_cell", "filepath": TMP_FILE,
                   "sheet": "", "cell": "B1", "column": "", "row": "",
                   "value": "Idade", "skip_header": True, "variable_name": "r"})
    block.execute({"action": "append_row", "filepath": TMP_FILE,
                   "sheet": "", "cell": "", "column": "", "row": "",
                   "value": "Alice;30", "skip_header": True, "variable_name": "r"})
    block.execute({"action": "append_row", "filepath": TMP_FILE,
                   "sheet": "", "cell": "", "column": "", "row": "",
                   "value": "Bob;25", "skip_header": True, "variable_name": "r"})
    return TMP_FILE


# ── create ───────────────────────────────────────────────────────────────────

def test_create_arquivo(block):
    r = block.execute({"action": "create", "filepath": TMP_FILE,
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "r"})
    assert r["success"] is True
    assert os.path.exists(TMP_FILE)


def test_create_sem_filepath_retorna_erro(block):
    r = block.execute({"action": "create", "filepath": "",
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "r"})
    assert r["success"] is False


# ── write_cell ───────────────────────────────────────────────────────────────

def test_write_cell(block, arquivo_com_dados):
    r = block.execute({"action": "write_cell", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "C1", "column": "", "row": "",
                       "value": "Cidade", "skip_header": True, "variable_name": "r"})
    assert r["success"] is True
    assert "C1" in r["message"]


def test_write_cell_sem_cell_retorna_erro(block, arquivo_com_dados):
    r = block.execute({"action": "write_cell", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "x", "skip_header": True, "variable_name": "r"})
    assert r["success"] is False


# ── read_cell ────────────────────────────────────────────────────────────────

def test_read_cell(block, arquivo_com_dados, contexto):
    r = block.execute({"action": "read_cell", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "A1", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "celula"})
    assert r["success"] is True
    assert contexto["celula"] == "Nome"


# ── append_row ───────────────────────────────────────────────────────────────

def test_append_row(block, arquivo_com_dados, contexto):
    r = block.execute({"action": "append_row", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "Carlos;28", "skip_header": True, "variable_name": "r"})
    assert r["success"] is True
    # Verifica que o arquivo agora tem mais linhas lendo a planilha
    r2 = block.execute({"action": "read_sheet", "filepath": arquivo_com_dados,
                        "sheet": "", "cell": "", "column": "", "row": "",
                        "value": "", "skip_header": True, "variable_name": "planilha"})
    assert r2["success"] is True
    assert len(contexto["planilha"]) == 3  # Alice, Bob, Carlos


# ── read_sheet ───────────────────────────────────────────────────────────────

def test_read_sheet_retorna_lista_de_dicts(block, arquivo_com_dados, contexto):
    r = block.execute({"action": "read_sheet", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "dados"})
    assert r["success"] is True
    assert isinstance(contexto["dados"], list)
    assert len(contexto["dados"]) == 2
    assert contexto["dados"][0]["Nome"] == "Alice"


# ── read_column ──────────────────────────────────────────────────────────────

def test_read_column(block, arquivo_com_dados, contexto):
    r = block.execute({"action": "read_column", "filepath": arquivo_com_dados,
                       "sheet": "", "cell": "", "column": "A", "row": "",
                       "value": "", "skip_header": True, "variable_name": "nomes"})
    assert r["success"] is True
    assert "Alice" in contexto["nomes"]
    assert "Bob" in contexto["nomes"]


# ── arquivo inexistente ──────────────────────────────────────────────────────

def test_arquivo_inexistente_retorna_erro(block):
    r = block.execute({"action": "read_cell", "filepath": "nao_existe.xlsx",
                       "sheet": "", "cell": "A1", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "r"})
    assert r["success"] is False
    assert "não encontrado" in r["message"]


# ── ação inválida ────────────────────────────────────────────────────────────

def test_acao_invalida(block):
    r = block.execute({"action": "inventada", "filepath": TMP_FILE,
                       "sheet": "", "cell": "", "column": "", "row": "",
                       "value": "", "skip_header": True, "variable_name": "r"})
    assert r["success"] is False
