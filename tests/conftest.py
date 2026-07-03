"""
conftest.py — Configuração global dos testes do PyFlow RPA.

Este arquivo é carregado automaticamente pelo pytest antes de qualquer teste.
Ele garante que:
  1. O sys.path aponte para a raiz do projeto (para imports funcionarem)
  2. O contexto de variáveis seja limpo antes de cada teste
"""
import sys
import os
import pytest

# Garante que a raiz do projeto está no sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def limpar_contexto():
    """
    Fixture executada automaticamente antes de cada teste.
    Limpa o contexto de variáveis (ExtractTextBlock._context) para
    garantir que um teste não interfere no próximo.
    """
    from blocks.browser.extract_text import ExtractTextBlock
    ExtractTextBlock._context.clear()
    yield
    ExtractTextBlock._context.clear()


@pytest.fixture
def contexto():
    """
    Retorna o dict de contexto de variáveis para uso nos testes.
    Uso: def test_algo(contexto): contexto["minha_var"] = "valor"
    """
    from blocks.browser.extract_text import ExtractTextBlock
    return ExtractTextBlock._context
