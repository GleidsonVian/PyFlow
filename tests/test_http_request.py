"""
Testes do bloco HttpRequestBlock.
Usa unittest.mock para simular respostas HTTP sem fazer chamadas reais de rede.
Isso garante que os testes rodem sem internet e sem depender de APIs externas.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from blocks.integration.http_request import HttpRequestBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return HttpRequestBlock()


def _mock_response(status=200, json_data=None, text=""):
    """Cria um mock de resposta requests."""
    resp = MagicMock()
    resp.status_code = status
    resp.ok = (status < 400)
    resp.text = text or json.dumps(json_data or {})
    resp.json.return_value = json_data or {}
    resp.reason = "OK" if status < 400 else "Error"
    return resp


# ── GET básico ───────────────────────────────────────────────────────────────

def test_get_sucesso(block):
    mock_resp = _mock_response(200, {"cidade": "São Paulo", "cep": "01310-100"})
    with patch("requests.request", return_value=mock_resp):
        r = block.execute({
            "method": "GET",
            "url": "https://viacep.com.br/ws/01310100/json/",
            "headers": "",
            "body": "",
            "json_field": "",
            "variable_name": "resultado",
            "timeout": "10",
        })
    assert r["success"] is True
    assert ctx._context["resultado"] is not None


def test_get_extrai_campo_json(block):
    mock_resp = _mock_response(200, {"localidade": "São Paulo", "uf": "SP"})
    with patch("requests.request", return_value=mock_resp):
        r = block.execute({
            "method": "GET",
            "url": "https://viacep.com.br/ws/01310100/json/",
            "headers": "",
            "body": "",
            "json_field": "localidade",
            "variable_name": "cidade",
            "timeout": "10",
        })
    assert r["success"] is True
    assert ctx._context["cidade"] == "São Paulo"


def test_get_campo_aninhado_dot_notation(block):
    mock_resp = _mock_response(200, {"endereco": {"rua": "Av. Paulista"}})
    with patch("requests.request", return_value=mock_resp):
        r = block.execute({
            "method": "GET",
            "url": "https://api.exemplo.com",
            "headers": "",
            "body": "",
            "json_field": "endereco.rua",
            "variable_name": "rua",
            "timeout": "10",
        })
    assert r["success"] is True
    assert ctx._context["rua"] == "Av. Paulista"


# ── POST ─────────────────────────────────────────────────────────────────────

def test_post_com_body(block):
    mock_resp = _mock_response(201, {"id": 42, "status": "criado"})
    with patch("requests.request", return_value=mock_resp):
        r = block.execute({
            "method": "POST",
            "url": "https://api.exemplo.com/items",
            "headers": '{"Content-Type": "application/json"}',
            "body": '{"nome": "teste"}',
            "json_field": "id",
            "variable_name": "novo_id",
            "timeout": "10",
        })
    assert r["success"] is True
    # O bloco salva o valor JSON sem converter para string
    assert ctx._context["novo_id"] == 42


# ── erros de validação ───────────────────────────────────────────────────────

def test_url_obrigatoria(block):
    r = block.execute({
        "method": "GET", "url": "",
        "headers": "", "body": "",
        "json_field": "", "variable_name": "r", "timeout": "10",
    })
    assert r["success"] is False


def test_headers_json_invalido_retorna_erro(block):
    r = block.execute({
        "method": "GET",
        "url": "https://api.exemplo.com",
        "headers": "{chave_sem_aspas: valor}",
        "body": "",
        "json_field": "",
        "variable_name": "r",
        "timeout": "10",
    })
    assert r["success"] is False


# ── erro de rede ─────────────────────────────────────────────────────────────

def test_timeout_retorna_erro(block):
    import requests
    with patch("requests.request", side_effect=requests.Timeout("tempo esgotado")):
        r = block.execute({
            "method": "GET",
            "url": "https://api.lenta.com",
            "headers": "",
            "body": "",
            "json_field": "",
            "variable_name": "r",
            "timeout": "1",
        })
    assert r["success"] is False
    assert "timeout" in r["message"].lower() or "tempo" in r["message"].lower()


def test_status_4xx_retorna_erro(block):
    # O bloco checa status_code >= 400 diretamente (não usa raise_for_status)
    mock_resp = _mock_response(404, {"error": "not found"})
    mock_resp.reason = "Not Found"
    with patch("requests.request", return_value=mock_resp):
        r = block.execute({
            "method": "GET",
            "url": "https://api.exemplo.com/naoexiste",
            "headers": "",
            "body": "",
            "json_field": "",
            "variable_name": "r",
            "timeout": "10",
        })
    assert r["success"] is False
    assert "404" in r["message"]
