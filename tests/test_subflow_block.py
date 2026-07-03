"""
Testes do bloco SubfluxoBlock (Executar outro Fluxo).
Usa mock para simular a leitura de JSON e o _build_steps sem precisar
carregar o registry completo (que tem dependências pesadas como cv2).
"""
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from blocks.control.subflow_block import SubfluxoBlock
from blocks.browser.extract_text import ExtractTextBlock as ctx


@pytest.fixture
def block():
    return SubfluxoBlock()


FLOW_SIMPLES = {
    "flow_name": "subfluxo_teste",
    "steps": [
        {
            "block": "SetVariableBlock",
            "_id": "s1", "_index": 0,
            "params": {"variable_name": "resultado_sub", "operation": "set", "value": "ok"},
            "_next_success": None, "_next_error": None,
        }
    ]
}


def _step_set(var, val):
    """Cria um step de SetVariable pronto para o runner."""
    from blocks.control.set_variable import SetVariableBlock
    return {
        "id": "s1", "block_instance": SetVariableBlock(),
        "params": {"variable_name": var, "operation": "set", "value": val},
        "next_success": None, "next_error": None, "_index": 0,
    }


def test_subfluxo_executa_e_exporta_variaveis(block):
    """Subfluxo define uma variável que deve aparecer no contexto pai."""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(FLOW_SIMPLES))), \
         patch.object(SubfluxoBlock, "_build_steps", return_value=[_step_set("resultado_sub", "ok")]):
        r = block.execute({
            "flow_name": "subfluxo_teste",
            "share_variables": True,
            "export_variables": True,
            "stop_on_failure": True,
            "flows_dir": "flows",
        })
    assert r["success"] is True
    assert ctx._context.get("resultado_sub") == "ok"


def test_subfluxo_salva_metadados_no_contexto(block):
    """Após execução, deve salvar {nome}_ok, {nome}_total, {nome}_status."""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(FLOW_SIMPLES))), \
         patch.object(SubfluxoBlock, "_build_steps", return_value=[_step_set("resultado_sub", "ok")]):
        block.execute({
            "flow_name": "subfluxo_teste",
            "share_variables": True,
            "export_variables": True,
            "stop_on_failure": True,
            "flows_dir": "flows",
        })
    assert ctx._context.get("subfluxo_teste_status") == "sucesso"
    assert ctx._context.get("subfluxo_teste_total") == "1"


def test_subfluxo_inexistente_retorna_erro(block):
    with patch("os.path.exists", return_value=False):
        r = block.execute({
            "flow_name": "nao_existe",
            "share_variables": True,
            "export_variables": True,
            "stop_on_failure": True,
            "flows_dir": "flows",
        })
    assert r["success"] is False
    assert "nao_existe" in r["message"]


def test_nome_obrigatorio(block):
    r = block.execute({
        "flow_name": "",
        "share_variables": True,
        "export_variables": True,
        "stop_on_failure": True,
        "flows_dir": "flows",
    })
    assert r["success"] is False


def test_subfluxo_vazio_retorna_sucesso(block):
    flow_vazio = {"flow_name": "vazio", "steps": []}
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(flow_vazio))):
        r = block.execute({
            "flow_name": "vazio",
            "share_variables": True,
            "export_variables": True,
            "stop_on_failure": True,
            "flows_dir": "flows",
        })
    assert r["success"] is True
    assert "0 passos" in r["message"]
