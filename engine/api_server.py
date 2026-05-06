"""
PyFlow RPA — API REST local (FastAPI + Uvicorn)
Servidor que roda em background e expõe endpoints HTTP
para disparar fluxos de qualquer sistema externo.

Coloque em: engine/api_server.py
"""
import threading
import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

# ── Estado global ──────────────────────────────────────────────────────

_state = {
    "running":      False,
    "current_flow": None,
    "history":      [],
    "started_at":   None,
}

_run_callback  = None
_stop_callback = None
_flows_dir     = "flows"

# Payloads recebidos via webhook (inbound) — acessíveis nos fluxos como variáveis
_webhook_inbox: dict = {}   # {"flow_name": {payload mais recente}}

app = FastAPI(title="PyFlow RPA", version="1.0.0", docs_url="/docs", redoc_url=None)


# ── Helpers ────────────────────────────────────────────────────────────

def _flow_path(name: str) -> str | None:
    candidates = [
        name,
        os.path.join(_flows_dir, name),
        os.path.join(_flows_dir, name + ".json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
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
    _state["history"] = _state["history"][:50]


# ── Schemas ────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    flow: str


class WebhookTriggerRequest(BaseModel):
    flow: str
    payload: dict = {}


# ── Endpoints ──────────────────────────────────────────────────────────

@app.get("/", response_class=JSONResponse)
def index():
    return {
        "app":      "PyFlow RPA API",
        "version":  "1.0.0",
        "status":   "running" if _state["running"] else "idle",
        "uptime":   _state["started_at"],
        "docs":     "/docs",
        "endpoints": [
            "GET  /flows",
            "POST /run",
            "GET  /status",
            "GET  /history",
            "POST /stop",
            "GET  /dashboard",
        ],
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Painel web de monitoramento do PyFlow RPA."""
    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PyFlow RPA — Dashboard</title>
<style>
  :root {
    --bg: #1e1e2e; --surface: #181825; --overlay: #313244;
    --muted: #45475a; --subtle: #6c7086; --text: #cdd6f4;
    --accent: #cba6f7; --green: #a6e3a1; --blue: #89b4fa;
    --red: #f38ba8; --orange: #fab387; --border: #313244;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; font-size: 14px; }

  header {
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 16px 28px; display: flex; align-items: center; gap: 14px;
  }
  header h1 { font-size: 20px; color: var(--accent); font-weight: 700; }
  header .uptime { font-size: 11px; color: var(--subtle); margin-left: auto; }
  header a.docs-link {
    font-size: 11px; color: var(--blue); text-decoration: none;
    border: 1px solid var(--blue); border-radius: 4px; padding: 3px 10px;
    margin-left: 8px;
  }
  header a.docs-link:hover { background: rgba(137,180,250,.12); }

  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
  }
  .badge.running { background: #1c3a2a; color: var(--green); border: 1px solid var(--green); }
  .badge.idle    { background: #2a2a3a; color: var(--subtle); border: 1px solid var(--muted); }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.running { background: var(--green); animation: pulse 1.2s infinite; }
  .dot.idle    { background: var(--muted); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  main { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 24px 28px; max-width: 1200px; }

  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px;
  }
  .card h2 { font-size: 13px; font-weight: 700; color: var(--accent); margin-bottom: 14px; letter-spacing: .5px; text-transform: uppercase; }

  .status-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .current-flow { font-size: 16px; font-weight: 600; color: var(--text); }
  .no-flow { color: var(--subtle); font-style: italic; }

  .flow-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 12px; border-radius: 8px; margin-bottom: 6px;
    background: var(--overlay); gap: 10px;
  }
  .flow-name { font-size: 13px; color: var(--text); flex: 1; }
  .flow-meta { font-size: 11px; color: var(--subtle); white-space: nowrap; }
  .btn-run {
    background: var(--green); color: #1e1e2e; border: none;
    border-radius: 6px; padding: 5px 14px; font-size: 12px;
    font-weight: 700; cursor: pointer; white-space: nowrap;
    transition: opacity .15s;
  }
  .btn-run:hover { opacity: .85; }
  .btn-run:disabled { background: var(--muted); color: var(--subtle); cursor: default; }
  .btn-stop {
    background: var(--red); color: #1e1e2e; border: none;
    border-radius: 6px; padding: 6px 18px; font-size: 13px;
    font-weight: 700; cursor: pointer; margin-top: 12px;
    transition: opacity .15s; width: 100%;
  }
  .btn-stop:hover { opacity: .85; }

  .history-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: 6px; margin-bottom: 5px;
    background: var(--overlay);
  }
  .history-icon { font-size: 14px; width: 20px; text-align: center; }
  .history-flow { flex: 1; font-size: 12px; color: var(--text); }
  .history-time { font-size: 11px; color: var(--subtle); white-space: nowrap; }
  .history-msg  { font-size: 11px; color: var(--subtle); display: block; margin-top: 2px; }

  .empty { color: var(--subtle); font-size: 13px; font-style: italic; padding: 8px 0; }
  .refresh-note { font-size: 11px; color: var(--subtle); margin-top: 8px; text-align: right; }
  #last-refresh { color: var(--accent); }
  .full-width { grid-column: 1 / -1; }

  #toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--overlay); border: 1px solid var(--accent);
    border-radius: 8px; padding: 12px 20px; color: var(--text);
    font-size: 13px; display: none; z-index: 999;
  }
</style>
</head>
<body>
<header>
  <span style="font-size:22px">⚡</span>
  <h1>PyFlow RPA</h1>
  <span id="header-badge" class="badge idle"><span class="dot idle"></span>idle</span>
  <span class="uptime">Iniciado em: <span id="uptime">—</span></span>
  <a class="docs-link" href="/docs" target="_blank">📖 Swagger UI</a>
</header>

<main>
  <div class="card">
    <h2>Status da Execução</h2>
    <div class="status-row">
      <span id="status-badge" class="badge idle"><span class="dot idle"></span>idle</span>
      <span id="current-flow" class="no-flow">Nenhum fluxo em execução</span>
    </div>
    <button class="btn-stop" id="btn-stop" onclick="stopFlow()">■  Parar execução</button>
  </div>

  <div class="card">
    <h2>Fluxos Disponíveis</h2>
    <div id="flows-list"><span class="empty">Carregando...</span></div>
  </div>

  <div class="card full-width">
    <h2>Histórico de Execuções</h2>
    <div id="history-list"><span class="empty">Carregando...</span></div>
    <p class="refresh-note">Atualização automática a cada 3s — último: <span id="last-refresh">—</span></p>
  </div>
</main>

<div id="toast"></div>

<script>
function showToast(msg, ms=2500) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', ms);
}
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}
function setBadge(el, running) {
  el.className = 'badge ' + (running ? 'running' : 'idle');
  el.innerHTML = '<span class="dot '+(running?'running':'idle')+'"></span>'+(running?'executando':'idle');
}
async function refresh() {
  try {
    const [status, flows, hist] = await Promise.all([
      fetchJSON('/status'), fetchJSON('/flows'), fetchJSON('/history')
    ]);
    setBadge(document.getElementById('header-badge'), status.status==='running');
    setBadge(document.getElementById('status-badge'), status.status==='running');
    const cf = document.getElementById('current-flow');
    if (status.current_flow) {
      cf.textContent = status.current_flow; cf.className = 'current-flow';
    } else {
      cf.textContent = 'Nenhum fluxo em execução'; cf.className = 'no-flow';
    }
    document.getElementById('uptime').textContent = status.uptime || '—';
    document.getElementById('btn-stop').disabled = status.status !== 'running';

    const fl = document.getElementById('flows-list');
    if (!flows.flows.length) {
      fl.innerHTML = '<span class="empty">Nenhum fluxo salvo encontrado.</span>';
    } else {
      fl.innerHTML = flows.flows.map(f => `
        <div class="flow-item">
          <span class="flow-name">📄 ${f.name}</span>
          <span class="flow-meta">${f.steps} blocos</span>
          <button class="btn-run" onclick="runFlow('${f.name.replace(/'/g,"\\\\'")}')"
            ${status.status==='running'?'disabled':''}>▶ Executar</button>
        </div>`).join('');
    }

    const hl = document.getElementById('history-list');
    if (!hist.history.length) {
      hl.innerHTML = '<span class="empty">Nenhuma execução registrada ainda.</span>';
    } else {
      hl.innerHTML = hist.history.map(h => `
        <div class="history-item">
          <span class="history-icon">${h.success ? '✅' : '❌'}</span>
          <span class="history-flow">
            ${h.flow}
            <span class="history-msg">${h.message || ''}</span>
          </span>
          <span class="history-time">${h.timestamp}</span>
        </div>`).join('');
    }
    document.getElementById('last-refresh').textContent = new Date().toLocaleTimeString('pt-BR');
  } catch(e) { console.error('Refresh error:', e); }
}
async function runFlow(name) {
  try {
    const r = await fetch('/run', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({flow: name})
    });
    const data = await r.json();
    showToast(data.success ? '▶ ' + data.message : '❌ ' + (data.detail || data.error));
    refresh();
  } catch(e) { showToast('Erro: ' + e.message); }
}
async function stopFlow() {
  try {
    const r = await fetch('/stop', {method:'POST'});
    const data = await r.json();
    showToast(data.success ? '■ Parada solicitada' : '❌ ' + (data.detail || data.error));
    refresh();
  } catch(e) { showToast('Erro: ' + e.message); }
}
refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/flows")
def list_flows():
    flows = _list_flows()
    return {"flows": flows, "total": len(flows)}


@app.post("/run")
def run_flow(body: RunRequest):
    global _run_callback

    if _state["running"]:
        raise HTTPException(409, detail=f"Fluxo '{_state['current_flow']}' já está em execução.")

    if not _run_callback:
        raise HTTPException(503, detail="PyFlow não está pronto para executar fluxos.")

    flow_name = body.flow.strip()
    if not flow_name:
        raise HTTPException(400, detail="Campo 'flow' é obrigatório.")

    path = _flow_path(flow_name)
    if not path:
        raise HTTPException(404, detail=f"Fluxo '{flow_name}' não encontrado em flows/.")

    try:
        with open(path, encoding="utf-8") as f:
            flow_data = json.load(f)
        display_name = flow_data.get("flow_name", flow_name)
    except Exception as e:
        raise HTTPException(500, detail=f"Erro ao ler fluxo: {str(e)}")

    _state["running"]      = True
    _state["current_flow"] = display_name

    threading.Thread(
        target=_run_callback,
        args=(path,),
        daemon=True,
    ).start()

    return {
        "success":    True,
        "message":    f"Fluxo '{display_name}' disparado.",
        "flow":       display_name,
        "started_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


@app.get("/status")
def status():
    return {
        "status":       "running" if _state["running"] else "idle",
        "current_flow": _state["current_flow"],
        "uptime":       _state["started_at"],
    }


@app.get("/history")
def history(limit: int = 20):
    limit = min(limit, 50)
    return {
        "history": _state["history"][:limit],
        "total":   len(_state["history"]),
    }


@app.post("/stop")
def stop_flow():
    global _stop_callback

    if not _state["running"]:
        raise HTTPException(400, detail="Nenhum fluxo em execução.")

    if _stop_callback:
        _stop_callback()

    return {"success": True, "message": "Sinal de parada enviado."}


# ── Webhook Inbound ────────────────────────────────────────────────────

@app.post("/webhook/{flow_name}")
async def webhook_trigger(flow_name: str, request: Request):
    """
    Recebe um POST externo e dispara o fluxo indicado.
    O payload JSON enviado fica disponível como variáveis no contexto:
      - webhook_payload  → dict completo
      - webhook_*        → cada campo de primeiro nível vira uma variável
    Exemplo: POST /webhook/meu_fluxo  Body: {"nome": "Gleidson", "valor": 42}
    Resulta em: webhook_nome="Gleidson", webhook_valor="42", webhook_payload={...}
    """
    global _run_callback, _webhook_inbox

    # Lê o payload (aceita JSON ou body vazio)
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {"data": payload}
    except Exception:
        payload = {}

    # Salva payload no inbox para ser lido pelo runner
    _webhook_inbox[flow_name] = payload

    # Injeta no contexto de variáveis imediatamente
    try:
        from blocks.browser.extract_text import ExtractTextBlock
        ExtractTextBlock._context["webhook_payload"] = payload
        for k, v in payload.items():
            ExtractTextBlock._context[f"webhook_{k}"] = str(v) if not isinstance(v, (list, dict)) else v
    except Exception:
        pass

    # Dispara o fluxo se não estiver rodando
    if _state["running"]:
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": f"Fluxo '{_state['current_flow']}' já está em execução. Payload salvo no contexto."}
        )

    if not _run_callback:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "PyFlow não está pronto para executar fluxos."}
        )

    path = _flow_path(flow_name)
    if not path:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": f"Fluxo '{flow_name}' não encontrado em flows/."}
        )

    try:
        with open(path, encoding="utf-8") as f:
            flow_data = json.load(f)
        display_name = flow_data.get("flow_name", flow_name)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erro ao ler fluxo: {str(e)}"}
        )

    _state["running"]      = True
    _state["current_flow"] = display_name

    threading.Thread(
        target=_run_callback,
        args=(path,),
        daemon=True,
    ).start()

    return {
        "success":    True,
        "message":    f"Webhook recebido — fluxo '{display_name}' disparado.",
        "flow":       display_name,
        "payload":    payload,
        "variables":  [f"webhook_{k}" for k in payload.keys()] + ["webhook_payload"],
        "started_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


@app.get("/webhook/inbox")
def webhook_inbox():
    """Retorna os últimos payloads recebidos via webhook (para debug)."""
    return {"inbox": _webhook_inbox, "total": len(_webhook_inbox)}


# ── Controle do servidor ───────────────────────────────────────────────

class ApiServer:
    """Gerencia o ciclo de vida do servidor FastAPI/Uvicorn em thread daemon."""

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
        # Encontra uma porta livre a partir da porta preferida
        self.port = self._find_free_port(self.port)
        _state["started_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False

    @staticmethod
    def _find_free_port(start: int, max_tries: int = 20) -> int:
        """Retorna a primeira porta livre a partir de `start`."""
        import socket
        for port in range(start, start + max_tries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # connect_ex retorna 0 se a porta ESTÁ em uso
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port  # porta livre
        return start  # fallback

    def _run(self):
        import uvicorn
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="error",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def is_active(self) -> bool:
        return self._active


# ── Singleton ──────────────────────────────────────────────────────────

_server_instance: Optional[ApiServer] = None


def get_api_server() -> ApiServer:
    global _server_instance
    if _server_instance is None:
        _server_instance = ApiServer()
    return _server_instance
