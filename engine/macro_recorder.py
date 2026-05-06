"""
Macro Recorder — captura ações do usuário no navegador e converte em blocos PyFlow.

Clique ESQUERDO  → listener JS (click event) → ClickElementBlock / FillFieldBlock
Clique DIREITO   → pynput (nível de SO) + elementFromPoint → QMenu nativo Python
                   Bypass total do Chrome — não depende de eventos JS para botão direito.
"""

import threading
import time
from typing import Callable

from blocks.browser.open_browser import OpenBrowserBlock


# ── JavaScript injetado no Chrome ────────────────────────────────────────────

# JS para cliques esquerdos, digitação e navegação (funciona normalmente)
_RECORDER_JS = r"""
(function() {
    if (window.__pyflow_recorder) return;
    window.__pyflow_recorder = { events: [], active: true };

    function getSelector(el) {
        if (!el || el === document.body) return 'body';
        if (el.id) return '#' + CSS.escape(el.id);
        if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
        if (el.placeholder) return el.tagName.toLowerCase() + '[placeholder="' + el.placeholder.replace(/"/g,'\\"') + '"]';
        if (el.className && typeof el.className === 'string') {
            var cls = el.className.trim().split(/\s+/).filter(Boolean).slice(0,2);
            if (cls.length) return el.tagName.toLowerCase() + '.' + cls.map(function(c){return CSS.escape(c);}).join('.');
        }
        if (el.getAttribute('data-testid'))
            return el.tagName.toLowerCase() + '[data-testid="' + el.getAttribute('data-testid') + '"]';
        if (el.getAttribute('aria-label'))
            return el.tagName.toLowerCase() + '[aria-label="' + el.getAttribute('aria-label').replace(/"/g,'\\"') + '"]';
        var path = [], node = el;
        while (node && node.nodeType === 1 && node.tagName !== 'BODY') {
            var idx=1, sib=node.previousSibling;
            while(sib){if(sib.nodeType===1&&sib.tagName===node.tagName)idx++;sib=sib.previousSibling;}
            path.unshift(node.tagName.toLowerCase()+(idx>1?':nth-of-type('+idx+')':''));
            node=node.parentNode;
        }
        return path.join(' > ');
    }

    // Clique esquerdo
    document.addEventListener('click', function(e) {
        if (!window.__pyflow_recorder.active) return;
        if (e.button !== 0) return;
        var el = e.target;
        window.__pyflow_recorder.events.push({
            type: 'click',
            selector: getSelector(el),
            label: (el.innerText||'').trim().replace(/\s+/g,' ').substring(0,60),
            tag: el.tagName.toLowerCase(),
            ts: Date.now()
        });
    }, true);

    // Digitação
    document.addEventListener('input', function(e) {
        if (!window.__pyflow_recorder.active) return;
        var el = e.target, tag = el.tagName.toLowerCase();
        if (tag!=='input'&&tag!=='textarea'&&tag!=='select') return;
        if (el.type==='password'||el.type==='hidden') return;
        window.__pyflow_recorder.events.push({
            type: 'input', selector: getSelector(el), value: el.value, ts: Date.now()
        });
    }, true);

    // Enter / Tab
    document.addEventListener('keydown', function(e) {
        if (!window.__pyflow_recorder.active) return;
        if (e.key==='Enter'||e.key==='Tab')
            window.__pyflow_recorder.events.push({type:'key', key:e.key, ts:Date.now()});
    }, true);

    // Suprime menu nativo do Chrome quando PyFlow está gravando
    document.addEventListener('contextmenu', function(e) {
        if (window.__pyflow_recorder && window.__pyflow_recorder.active) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, true);
})();
"""

# JS para obter informações do elemento em uma coordenada da viewport
_ELEMENT_AT_POINT_JS = """
(function(vx, vy) {
    var el = document.elementFromPoint(vx, vy);
    if (!el || el === document.body) return null;

    function getSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
        if (el.placeholder) return el.tagName.toLowerCase() + '[placeholder="' + el.placeholder.replace(/"/g,'\\"') + '"]';
        if (el.className && typeof el.className === 'string') {
            var cls = el.className.trim().split(/\\s+/).filter(Boolean).slice(0,2);
            if (cls.length) return el.tagName.toLowerCase() + '.' + cls.map(function(c){return CSS.escape(c);}).join('.');
        }
        if (el.getAttribute('data-testid'))
            return el.tagName.toLowerCase() + '[data-testid="' + el.getAttribute('data-testid') + '"]';
        if (el.getAttribute('aria-label'))
            return el.tagName.toLowerCase() + '[aria-label="' + el.getAttribute('aria-label').replace(/"/g,'\\"') + '"]';
        var path = [], node = el;
        while (node && node.nodeType === 1 && node.tagName !== 'BODY') {
            var idx=1, sib=node.previousSibling;
            while(sib){if(sib.nodeType===1&&sib.tagName===node.tagName)idx++;sib=sib.previousSibling;}
            path.unshift(node.tagName.toLowerCase()+(idx>1?':nth-of-type('+idx+')':''));
            node=node.parentNode;
        }
        return path.join(' > ');
    }

    function getAttrs(el) {
        var want = ['href','src','value','alt','title','data-id','data-value',
                    'data-name','aria-label','placeholder','type','action'];
        return want.filter(function(a){ var v=el.getAttribute(a); return v&&v.length<300; });
    }

    var selector = getSelector(el);
    var isList = false;
    try { isList = document.querySelectorAll(selector).length > 1; } catch(x){}

    return {
        selector: selector,
        tag: el.tagName.toLowerCase(),
        text: (el.innerText||'').trim().replace(/\\s+/g,' ').substring(0,80),
        attrs: getAttrs(el),
        is_list: isList
    };
})(arguments[0], arguments[1]);
"""

_FLUSH_JS = """
(function(){
    if (!window.__pyflow_recorder) return [];
    return window.__pyflow_recorder.events.splice(0);
})();
"""

_STOP_JS = """
(function(){
    if (window.__pyflow_recorder) {
        window.__pyflow_recorder.active = false;
        window.__pyflow_recorder.events = [];
        delete window.__pyflow_recorder;
    }
})();
"""

# JS para obter posição da janela Chrome e info de escala
_WINDOW_INFO_JS = """
return {
    screenX:         window.screenX,
    screenY:         window.screenY,
    outerWidth:      window.outerWidth,
    outerHeight:     window.outerHeight,
    innerWidth:      window.innerWidth,
    innerHeight:     window.innerHeight,
    devicePixelRatio: window.devicePixelRatio || 1
};
"""


# ── MacroRecorder ─────────────────────────────────────────────────────────────

class MacroRecorder:
    """
    Grava ações do usuário no Chrome.

    Clique direito é capturado via pynput (OS-level) + Selenium elementFromPoint.
    Clique esquerdo, inputs e teclas são capturados via JS.
    """

    def __init__(
        self,
        on_action: Callable[[dict], None],
        on_context_menu: Callable[[dict], None],
        on_url_change: Callable[[str], None],
        on_error: Callable[[str], None] | None = None,
    ):
        self._on_action       = on_action
        self._on_context_menu = on_context_menu
        self._on_url_change   = on_url_change
        self._on_error        = on_error or (lambda m: None)

        self._running = False
        self._poll_thread: threading.Thread | None = None
        self._mouse_listener = None
        self._last_url = ""
        self._pending_inputs: dict[str, str] = {}

    def start(self) -> None:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            raise RuntimeError(
                "Nenhum navegador aberto.\n"
                "Adicione e execute o bloco 'Abrir Navegador' antes de gravar."
            )
        self._running  = True
        self._last_url = driver.current_url
        driver.execute_script(_RECORDER_JS)

        # Polling de eventos JS (cliques esquerdos, inputs)
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        # Listener de clique direito a nível de SO (pynput)
        self._start_mouse_listener()

    def stop(self) -> None:
        self._running = False
        self._flush_pending_inputs()

        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        try:
            driver = OpenBrowserBlock.get_driver()
            if driver:
                driver.execute_script(_STOP_JS)
        except Exception:
            pass

        if self._poll_thread:
            self._poll_thread.join(timeout=2)
            self._poll_thread = None

    # ── Listener de mouse (pynput) ────────────────────────────────────

    def _start_mouse_listener(self) -> None:
        try:
            from pynput import mouse as pynput_mouse

            def on_click(x, y, button, pressed):
                if not pressed or not self._running:
                    return
                if button == pynput_mouse.Button.right:
                    self._handle_right_click(x, y)

            self._mouse_listener = pynput_mouse.Listener(on_click=on_click)
            self._mouse_listener.start()
        except ImportError:
            self._on_error(
                "pynput não encontrado. Instale com: pip install pynput\n"
                "Clique direito não funcionará."
            )
        except Exception as e:
            self._on_error(f"Erro ao iniciar listener de mouse: {e}")

    def _handle_right_click(self, screen_x: int, screen_y: int) -> None:
        """Chamado pelo pynput quando o usuário clica com botão direito."""
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return
        try:
            # Obtém posição e escala da janela do Chrome
            info = driver.execute_script(_WINDOW_INFO_JS)
            dpr         = info.get("devicePixelRatio", 1) or 1
            win_x       = info.get("screenX", 0)
            win_y       = info.get("screenY", 0)
            outer_h     = info.get("outerHeight", 0)
            inner_h     = info.get("innerHeight", 0)
            toolbar_h   = outer_h - inner_h   # altura da barra de endereços + abas

            # Converte coords de tela → coords da viewport
            viewport_x = (screen_x / dpr) - win_x
            viewport_y = (screen_y / dpr) - win_y - toolbar_h

            # Verifica se o clique foi dentro da área de conteúdo do Chrome
            if viewport_x < 0 or viewport_y < 0:
                return
            if viewport_x > info.get("innerWidth", 9999):
                return

            # Obtém o elemento nessa posição
            result = driver.execute_script(_ELEMENT_AT_POINT_JS, viewport_x, viewport_y)
            if not result:
                return

            result["type"] = "context_menu_request"
            self._flush_pending_inputs()
            self._on_context_menu(result)

        except Exception as e:
            if self._running:
                self._on_error(f"Erro no clique direito: {e}")

    # ── Polling de eventos JS ─────────────────────────────────────────

    def _poll_loop(self) -> None:
        driver = OpenBrowserBlock.get_driver()
        while self._running:
            try:
                url = driver.current_url
                if url != self._last_url:
                    self._flush_pending_inputs()
                    self._last_url = url
                    self._on_url_change(url)
                    try:
                        driver.execute_script(_RECORDER_JS)
                    except Exception:
                        pass

                events = driver.execute_script(_FLUSH_JS) or []
                if events:
                    self._process_events(events)
            except Exception as e:
                if self._running:
                    self._on_error(str(e))
            time.sleep(0.3)

    def _process_events(self, events: list[dict]) -> None:
        for ev in events:
            t = ev.get("type")
            if t == "input":
                self._pending_inputs[ev.get("selector","").strip()] = ev.get("value","")
            elif t == "click":
                self._flush_pending_inputs()
                self._on_action({
                    "type": "click",
                    "selector": ev.get("selector","").strip(),
                    "label":    ev.get("label",""),
                    "tag":      ev.get("tag",""),
                })
            elif t == "key":
                self._on_action({"type": "key", "key": ev.get("key","")})

    def _flush_pending_inputs(self) -> None:
        for sel, val in list(self._pending_inputs.items()):
            self._on_action({"type": "fill", "selector": sel, "value": val})
        self._pending_inputs.clear()


# ── Conversão ação → step PyFlow ──────────────────────────────────────────────

def action_to_step(action: dict) -> dict | None:
    t   = action.get("type")
    sel = action.get("selector", "")

    if t == "click":
        return {"block": "ClickElementBlock",
                "params": {"selector": sel, "timeout": "10"}}
    if t == "fill":
        return {"block": "FillFieldBlock",
                "params": {"selector": sel, "value": action.get("value",""),
                           "clear_before": True, "timeout": "10"}}
    if t == "navigate":
        return {"block": "NavigateToUrlBlock",
                "params": {"url": action.get("url","")}}
    if t == "key":
        keys = {"Enter": "RETURN", "Tab": "TAB"}
        return {"block": "PressKeyBlock",
                "params": {"key": keys.get(action.get("key",""), action.get("key",""))}}
    if t == "extract_text":
        return {"block": "ExtractTextBlock",
                "params": {"selector": sel, "variable_name": "texto_capturado",
                           "timeout": "10"}}
    if t == "extract_attr":
        return {"block": "ExtractTextBlock",
                "params": {"selector": sel, "attribute": action.get("attribute",""),
                           "variable_name": "atributo_capturado", "timeout": "10"}}
    if t == "extract_list":
        return {"block": "ExtractListBlock",
                "params": {"selector": sel, "variable_name": "lista_capturada",
                           "timeout": "10"}}
    if t == "smart_wait":
        return {"block": "SmartWaitBlock",
                "params": {"selector": sel, "condition": "visible", "timeout": "10"}}
    if t == "screenshot":
        return {"block": "ScreenshotBlock",
                "params": {"filename": "screenshot.png"}}
    return None


def action_label(action: dict) -> str:
    t   = action.get("type")
    sel = action.get("selector", "")
    s   = (sel[:42] + "...") if len(sel) > 42 else sel

    if t == "click":
        tag = action.get("tag","")
        icon = {"a":"[link]","button":"[btn]","input":"[input]","img":"[img]"}.get(tag,"[clique]")
        lbl = action.get("label") or s
        return f"{icon}  Clicar em  {lbl[:50]}"
    if t == "fill":
        val = action.get("value","")
        dv = (val[:28]+"...") if len(val)>28 else val
        return f'[campo]  Preencher  {s}  ->  "{dv}"'
    if t == "navigate":
        return f"[nav]  Navegar para  {action.get('url','')}"
    if t == "key":
        return f"[tecla]  {action.get('key','')}"
    if t == "extract_text":
        return f"[texto]  Coletar texto  de  {s}"
    if t == "extract_attr":
        return f"[attr]  Coletar [{action.get('attribute','')}]  de  {s}"
    if t == "extract_list":
        return f"[lista]  Extrair lista  de  {s}"
    if t == "smart_wait":
        return f"[wait]  Aguardar  {s}"
    if t == "screenshot":
        return "[foto]  Screenshot"
    return f"? {action}"
