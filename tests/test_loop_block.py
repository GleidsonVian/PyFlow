"""
Testes do bloco LoopBlock (Repetir).
Verifica que o bloco devolve os dados corretos para o runner
interpretar e repetir o escopo.
"""
import pytest
from blocks.control.loop_block import LoopBlock


@pytest.fixture
def block():
    return LoopBlock()


def test_loop_3x(block):
    r = block.execute({"times": "3", "delay_between": "0"})
    assert r["success"] is True
    assert r["data"]["loop"] is True
    assert r["data"]["times"] == 3


def test_loop_1x(block):
    r = block.execute({"times": "1", "delay_between": "0"})
    assert r["success"] is True
    assert r["data"]["times"] == 1


def test_loop_delay(block):
    r = block.execute({"times": "2", "delay_between": "0.5"})
    assert r["data"]["delay_between"] == 0.5


def test_loop_zero_repeticoes_retorna_erro(block):
    r = block.execute({"times": "0", "delay_between": "0"})
    assert r["success"] is False
    assert "1" in r["message"]  # mensagem fala em ≥ 1


def test_loop_negativo_retorna_erro(block):
    r = block.execute({"times": "-5", "delay_between": "0"})
    assert r["success"] is False


def test_loop_texto_nao_numerico_retorna_erro(block):
    r = block.execute({"times": "muitas", "delay_between": "0"})
    assert r["success"] is False


def test_loop_default_sem_delay(block):
    r = block.execute({"times": "3"})
    assert r["success"] is True
    assert r["data"]["delay_between"] == 0.0
