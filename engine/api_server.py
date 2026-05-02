"""
PyFlow RPA — API REST local
Servidor Flask que roda em background e expõe endpoints HTTP
para disparar fluxos de qualquer sistema externo.

Coloque em: engine/api_server.py
"""
import threading
import json
import os
from datetime import datetime
from flask import Flask, jsonify, request, abort

# ── Estado global da API ──────────────────────────────────────────────

_state = {
    "running":      False,        # fluxo em execução?
    "current_flow": None,         # nome do fluxo atual
    "history":      [],           # últimas execuções
    "started_at":   None,         # quando o servidor subiu
}

_run_callback  = None   # callable(flow_path) → injetado pelo MainWindow
_stop_callback = None   # callable() → injetado pelo MainWindow
_flows_dir     = "flows"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ── Helpers ───────────────────────────────────────────────────────────

def _flow_path(name: str) -> str | None:
    """Resolve nome do fluxo para caminho completo."""
    candidates = [
        name,
        os.path.join(_flows_dir, name),
        os.path.join(_flows_dir, name + ".json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _list_flows() -> list:
    if not os.path.exists(_flows_dir):
        return []
    flows = []
    for f in sorted(os.listdir(_flows_dir)):
        if not f.endswith(".json"):
            continue
        path = os.path.join(_flows_dir, f)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            flows.append({
                "name":       data.get("flow_name", f.replace(".json", "")),
                "file":       f,
                "steps":      len(data.get("steps", [])),
                "created_at": data.get("created_at", "")[:10],
            })
        except Exception:
            flows.append({"name": f, "file": f, "steps": 0, "created_at": ""})
    return flows


def _add_history(flow_name: str, success: bool, message: str = ""):
    entry = {
        "flow":      flow_name,
        "success":   success,
        "message":   message,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    _state["history"].insert(0, entry)
    _state["history"] = _state["history"][:50]   # mantém últimas 50


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def index():
    return jsonify({
        "app":      "PyFlow RPA API",
        "version":  "1.0.0",
        "status":   "running" if _state["running"] else "idle",
        "uptime":   _state["started_at"],
        "endpoints": [
            "GET  /flows",
            "POST /run",
            "GET  /status",
            "GET  /history",
            "POST /stop",
        ],
    })


@app.get("/flows")
def list_flows():
    """Lista todos os fluxos salvos na pasta flows/."""
    return jsonify({"flows": _list_flows(), "total": len(_list_flows())})


@app.post("/run")
def run_flow():
    """
    Dispara um fluxo pelo nome ou caminho.
    Body: { "flow": "nome_do_fluxo" }
    """
    global _run_callback

    if _state["running"]:
        return jsonify({
            "success": False,
            "error":   f"Fluxo '{_state['current_flow']}' já está em execução."
        }), 409

    if not _run_callback:
        return jsonify({
            "success": False,
            "error":   "PyFlow não está pronto para executar fluxos."
        }), 503

    data = request.get_json(silent=True) or {}
    flow_name = data.get("flow", "").strip()

    if not flow_name:
        return jsonify({"success": False, "error": "Campo 'flow' é obrigatório."}), 400

    path = _flow_path(flow_name)
    if not path:
        return jsonify({
            "success": False,
            "error":   f"Fluxo '{flow_name}' não encontrado em flows/."
        }), 404

    try:
        with open(path, encoding="utf-8") as f:
            flow_data = json.load(f)
        display_name = flow_data.get("flow_name", flow_name)
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro ao ler fluxo: {str(e)}"}), 500

    _state["running"]      = True
    _state["current_flow"] = display_name

    # Dispara na thread principal via callback
    _run_callback(path)

    return jsonify({
        "success":    True,
        "message":    f"Fluxo '{display_name}' disparado.",
        "flow":       display_name,
        "started_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    })


@app.get("/status")
def status():
    """Retorna o estado atual da execução."""
    return jsonify({
        "status":       "running" if _state["running"] else "idle",
        "current_flow": _state["current_flow"],
        "uptime":       _state["started_at"],
    })


@app.get("/history")
def history():
    """Retorna o histórico das últimas execuções."""
    limit = min(int(request.args.get("limit", 20)), 50)
    return jsonify({
        "history": _state["history"][:limit],
        "total":   len(_state["history"]),
    })


@app.post("/stop")
def stop_flow():
    """Para a execução atual."""
    global _stop_callback

    if not _state["running"]:
        return jsonify({"success": False, "error": "Nenhum fluxo em execução."}), 400

    if _stop_callback:
        _stop_callback()

    return jsonify({"success": True, "message": "Sinal de parada enviado."})


# ── Controle do servidor ──────────────────────────────────────────────

class ApiServer:
    """Gerencia o ciclo de vida do servidor Flask em thread daemon."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host    = host
        self.port    = port
        self._thread = None
        self._active = False

    def set_callbacks(self, run_cb, stop_cb, flows_dir: str = "flows"):
        global _run_callback, _stop_callback, _flows_dir
        _run_callback  = run_cb
        _stop_callback = stop_cb
        _flows_dir     = flows_dir

    def notify_started(self, flow_name: str):
        _state["running"]      = True
        _state["current_flow"] = flow_name

    def notify_finished(self, flow_name: str, success: bool, message: str = ""):
        _state["running"]      = False
        _state["current_flow"] = None
        _add_history(flow_name, success, message)

    def start(self):
        if self._active:
            return
        _state["started_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        # Flask não tem stop() limpo em modo desenvolvimento
        # O thread é daemon — encerra com o processo principal

    def _run(self):
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)   # silencia logs do Flask no console
        app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def is_active(self) -> bool:
        return self._active


# Instância global
_server = ApiServer()


def get_api_server() -> ApiServer:
    return _server
