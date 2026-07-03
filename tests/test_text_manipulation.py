"""
Testes do bloco TextManipulationBlock (Manipular Texto).
Cobre as 14 operações de transformação de strings.
"""
import pytest
from blocks.control.text_manipulation import TextManipulationBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return TextManipulationBlock()


def _exec(block, op, var_in="txt", p1="", p2="", var_out="resultado"):
    return block.execute({
        "input_variable": var_in,
        "operation": op,
        "param1": p1,
        "param2": p2,
        "output_variable": var_out,
    })


def test_upper(block):
    ctx._context["txt"] = "pyflow rpa"
    _exec(block, "upper")
    assert ctx._context["resultado"] == "PYFLOW RPA"


def test_lower(block):
    ctx._context["txt"] = "PYFLOW RPA"
    _exec(block, "lower")
    assert ctx._context["resultado"] == "pyflow rpa"


def test_trim(block):
    ctx._context["txt"] = "  espaços  "
    _exec(block, "trim")
    assert ctx._context["resultado"] == "espaços"


def test_replace(block):
    ctx._context["txt"] = "foo bar foo"
    _exec(block, "replace", p1="foo", p2="baz")
    assert ctx._context["resultado"] == "baz bar baz"


def test_regex_extract(block):
    ctx._context["txt"] = "Preço: R$ 49,90"
    _exec(block, "regex_extract", p1=r"\d+[,\.]\d+")
    assert ctx._context["resultado"] == "49,90"


def test_regex_extract_sem_match_retorna_vazio(block):
    ctx._context["txt"] = "nenhum número aqui"
    r = _exec(block, "regex_extract", p1=r"\d{4}")
    assert ctx._context.get("resultado", "") == ""


def test_split(block):
    ctx._context["txt"] = "a,b,c"
    _exec(block, "split", p1=",")
    assert ctx._context["resultado"] == ["a", "b", "c"]


def test_join(block):
    ctx._context["lista"] = ["x", "y", "z"]
    _exec(block, "join", var_in="lista", p1="-")
    assert ctx._context["resultado"] == "x-y-z"


def test_count_ocorrencias(block):
    ctx._context["txt"] = "banana"
    _exec(block, "count", p1="a")
    assert ctx._context["resultado"] == "3"


def test_count_comprimento_total(block):
    ctx._context["txt"] = "abc"
    _exec(block, "count", p1="")
    assert ctx._context["resultado"] == "3"


def test_contains_verdadeiro(block):
    ctx._context["txt"] = "automação"
    _exec(block, "contains", p1="ação")
    assert ctx._context["resultado"] == "True"


def test_contains_falso(block):
    ctx._context["txt"] = "automação"
    _exec(block, "contains", p1="xyz")
    assert ctx._context["resultado"] == "False"


def test_starts_with(block):
    ctx._context["txt"] = "PyFlow RPA"
    _exec(block, "starts_with", p1="PyFlow")
    assert ctx._context["resultado"] == "True"


def test_ends_with(block):
    ctx._context["txt"] = "PyFlow RPA"
    _exec(block, "ends_with", p1="RPA")
    assert ctx._context["resultado"] == "True"


def test_substring(block):
    ctx._context["txt"] = "PyFlow RPA"
    _exec(block, "substring", p1="0", p2="6")
    assert ctx._context["resultado"] == "PyFlow"


def test_length(block):
    ctx._context["txt"] = "abcde"
    _exec(block, "length")
    assert ctx._context["resultado"] == "5"


def test_variavel_inexistente_trata_como_vazio(block):
    # Bloco trata variável inexistente como string vazia e executa normalmente
    r = block.execute({
        "input_variable": "nao_existe_mesmo",
        "operation": "upper",
        "param1": "", "param2": "",
        "output_variable": "out",
    })
    assert r["success"] is True
    assert ctx._context.get("out", "") == ""
