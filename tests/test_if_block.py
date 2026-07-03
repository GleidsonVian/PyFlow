"""
Testes do bloco IfBlock (Condição Se).
Foco nas condições de variável (as de elemento requerem browser aberto).
"""
import pytest
from blocks.control.if_block import IfBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return IfBlock()


def _exec(block, ctype, var="x", expected=""):
    return block.execute({
        "condition_type": ctype,
        "variable_name": var,
        "expected_value": expected,
        "selector": "",
    })


# ── variable_equals ──────────────────────────────────────────────────────────

def test_equals_verdadeiro(block):
    ctx._context["x"] = "pyflow"
    r = _exec(block, "variable_equals", expected="pyflow")
    assert r["success"] is True
    assert r["data"]["if_result"] is True


def test_equals_falso(block):
    ctx._context["x"] = "pyflow"
    r = _exec(block, "variable_equals", expected="outro")
    assert r["data"]["if_result"] is False


def test_equals_case_insensitive(block):
    ctx._context["x"] = "PyFlow"
    r = _exec(block, "variable_equals", expected="pyflow")
    assert r["data"]["if_result"] is True


# ── variable_not_equals ──────────────────────────────────────────────────────

def test_not_equals(block):
    ctx._context["x"] = "a"
    r = _exec(block, "variable_not_equals", expected="b")
    assert r["data"]["if_result"] is True


# ── variable_contains ────────────────────────────────────────────────────────

def test_contains_verdadeiro(block):
    ctx._context["x"] = "automação com PyFlow RPA"
    r = _exec(block, "variable_contains", expected="PyFlow")
    assert r["data"]["if_result"] is True


def test_contains_falso(block):
    ctx._context["x"] = "texto qualquer"
    r = _exec(block, "variable_contains", expected="ausente")
    assert r["data"]["if_result"] is False


# ── variable_greater / variable_less ─────────────────────────────────────────

def test_greater(block):
    ctx._context["n"] = "10"
    r = _exec(block, "variable_greater", var="n", expected="5")
    assert r["data"]["if_result"] is True


def test_greater_falso(block):
    ctx._context["n"] = "3"
    r = _exec(block, "variable_greater", var="n", expected="5")
    assert r["data"]["if_result"] is False


def test_less(block):
    ctx._context["n"] = "2"
    r = _exec(block, "variable_less", var="n", expected="5")
    assert r["data"]["if_result"] is True


def test_comparacao_numerica_invalida_retorna_erro(block):
    ctx._context["x"] = "texto_nao_numero"
    r = _exec(block, "variable_greater", expected="5")
    assert r["success"] is False


# ── variable_empty / variable_not_empty ──────────────────────────────────────

def test_empty_verdadeiro(block):
    ctx._context["x"] = ""
    r = _exec(block, "variable_empty")
    assert r["data"]["if_result"] is True


def test_empty_falso(block):
    ctx._context["x"] = "tem valor"
    r = _exec(block, "variable_empty")
    assert r["data"]["if_result"] is False


def test_not_empty(block):
    ctx._context["x"] = "valor"
    r = _exec(block, "variable_not_empty")
    assert r["data"]["if_result"] is True


def test_variavel_inexistente_e_empty(block):
    # variável que não existe retorna "" → é considerada vazia
    r = _exec(block, "variable_empty", var="nao_existe")
    assert r["data"]["if_result"] is True


# ── tipo desconhecido ────────────────────────────────────────────────────────

def test_tipo_desconhecido_retorna_erro(block):
    r = _exec(block, "condicao_inventada")
    assert r["success"] is False
