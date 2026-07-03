"""
Testes do bloco SetVariableBlock (Definir Variável).
Cobre todas as 9 operações: set, increment, decrement, append,
prepend, multiply, divide, now, clear.
"""
import pytest
from blocks.control.set_variable import SetVariableBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return SetVariableBlock()


# ── set ──────────────────────────────────────────────────────────────────────

def test_set_valor_simples(block):
    r = block.execute({"variable_name": "nome", "operation": "set", "value": "PyFlow"})
    assert r["success"] is True
    assert ctx._context["nome"] == "PyFlow"


def test_set_sobrescreve_valor_anterior(block):
    ctx._context["x"] = "antigo"
    block.execute({"variable_name": "x", "operation": "set", "value": "novo"})
    assert ctx._context["x"] == "novo"


def test_set_valor_vazio(block):
    r = block.execute({"variable_name": "vazio", "operation": "set", "value": ""})
    assert r["success"] is True
    assert ctx._context["vazio"] == ""


# ── increment ────────────────────────────────────────────────────────────────

def test_increment_a_partir_de_zero(block):
    block.execute({"variable_name": "cont", "operation": "set", "value": "0"})
    block.execute({"variable_name": "cont", "operation": "increment", "value": ""})
    assert ctx._context["cont"] == "1"


def test_increment_valor_customizado(block):
    block.execute({"variable_name": "n", "operation": "set", "value": "10"})
    block.execute({"variable_name": "n", "operation": "increment", "value": "5"})
    assert ctx._context["n"] == "15"


def test_increment_sem_valor_inicial_vira_1(block):
    # variável não existe — deve virar 1
    block.execute({"variable_name": "novo_cont", "operation": "increment", "value": ""})
    assert ctx._context["novo_cont"] == "1"


# ── decrement ────────────────────────────────────────────────────────────────

def test_decrement_basico(block):
    block.execute({"variable_name": "n", "operation": "set", "value": "5"})
    block.execute({"variable_name": "n", "operation": "decrement", "value": ""})
    assert ctx._context["n"] == "4"


# ── append / prepend ─────────────────────────────────────────────────────────

def test_append(block):
    block.execute({"variable_name": "txt", "operation": "set", "value": "Olá"})
    block.execute({"variable_name": "txt", "operation": "append", "value": " Mundo"})
    assert ctx._context["txt"] == "Olá Mundo"


def test_prepend(block):
    block.execute({"variable_name": "txt", "operation": "set", "value": "Mundo"})
    block.execute({"variable_name": "txt", "operation": "prepend", "value": "Olá "})
    assert ctx._context["txt"] == "Olá Mundo"


# ── multiply / divide ────────────────────────────────────────────────────────

def test_multiply(block):
    block.execute({"variable_name": "n", "operation": "set", "value": "7"})
    block.execute({"variable_name": "n", "operation": "multiply", "value": "3"})
    assert ctx._context["n"] == "21"


def test_divide(block):
    block.execute({"variable_name": "n", "operation": "set", "value": "10"})
    block.execute({"variable_name": "n", "operation": "divide", "value": "2"})
    assert ctx._context["n"] == "5"


def test_divide_por_zero_retorna_erro(block):
    block.execute({"variable_name": "n", "operation": "set", "value": "10"})
    r = block.execute({"variable_name": "n", "operation": "divide", "value": "0"})
    assert r["success"] is False
    assert "zero" in r["message"].lower()


# ── now ──────────────────────────────────────────────────────────────────────

def test_now_salva_data(block):
    r = block.execute({
        "variable_name": "data_atual",
        "operation": "now",
        "value": "",
        "format": "%d/%m/%Y"
    })
    assert r["success"] is True
    assert "/" in ctx._context["data_atual"]  # formato dd/mm/yyyy


# ── clear ────────────────────────────────────────────────────────────────────

def test_clear_remove_variavel(block):
    ctx._context["remover"] = "qualquer coisa"
    r = block.execute({"variable_name": "remover", "operation": "clear", "value": ""})
    assert r["success"] is True
    assert "remover" not in ctx._context


def test_clear_variavel_inexistente_nao_explode(block):
    r = block.execute({"variable_name": "nao_existe", "operation": "clear", "value": ""})
    assert r["success"] is True


# ── validação ────────────────────────────────────────────────────────────────

def test_nome_obrigatorio(block):
    r = block.execute({"variable_name": "", "operation": "set", "value": "x"})
    assert r["success"] is False


def test_operacao_invalida(block):
    r = block.execute({"variable_name": "x", "operation": "voar", "value": ""})
    assert r["success"] is False
    assert "inválida" in r["message"].lower() or "inválid" in r["message"]
