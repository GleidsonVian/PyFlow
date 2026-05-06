"""
Gravador de seletores CSS com clique visual — PyFlow RPA.
Injeta um overlay JavaScript no Chrome ativo.
O usuário passa o mouse nos elementos (highlight azul) e clica para capturar.
ui/selector_picker.py
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QApplication,
    QWidget, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont


# ── JavaScript injetado no Chrome ─────────────────────────────────────────────

_PICKER_JS = """
(function() {
  if (window._pyflow_picker_active) return 'already_active';

  window._pyflow_picker_active  = true;
  window._pyflow_selector       = null;
  window._pyflow_hover_selector = null;

  /* ── Highlight box ─────────────────────────────── */
  const hl = document.createElement('div');
  hl.id = '_pyflow_hl';
  hl.style.cssText = [
    'position:fixed', 'pointer-events:none', 'z-index:2147483646',
    'border:2px solid #89b4fa', 'background:rgba(137,180,250,0.15)',
    'box-sizing:border-box', 'transition:all 0.08s ease',
    'border-radius:3px'
  ].join(';');

  /* ── Tooltip ───────────────────────────────────── */
  const tip = document.createElement('div');
  tip.id = '_pyflow_tip';
  tip.style.cssText = [
    'position:fixed', 'z-index:2147483647', 'pointer-events:none',
    'background:#1e1e2e', 'color:#89b4fa',
    'font:12px/1.4 Consolas,monospace',
    'padding:5px 10px', 'border-radius:5px',
    'border:1px solid #313244',
    'max-width:480px', 'word-break:break-all',
    'box-shadow:0 4px 16px rgba(0,0,0,0.5)'
  ].join(';');

  /* ── Banner de instrução ───────────────────────── */
  const banner = document.createElement('div');
  banner.style.cssText = [
    'position:fixed', 'top:0', 'left:0', 'right:0',
    'z-index:2147483647', 'pointer-events:none',
    'background:rgba(203,166,247,0.95)', 'color:#1e1e2e',
    'font:700 13px Segoe UI,sans-serif',
    'text-align:center', 'padding:8px',
    'letter-spacing:.3px'
  ].join(';');
  banner.textContent = '📍 PyFlow — Clique no elemento para capturar o seletor CSS  |  Esc para cancelar';

  document.body.appendChild(hl);
  document.body.appendChild(tip);
  document.body.appendChild(banner);

  /* ── Gerador de seletor CSS estável ─────────────── */
  function escape(s) {
    try { return CSS.escape(s); } catch(e) { return s.replace(/[^a-zA-Z0-9_-]/g, '\\\\$&'); }
  }

  function getSelector(el) {
    if (!el || el === document.body || el === document.documentElement)
      return 'body';

    // 1. ID
    if (el.id && /^[a-zA-Z]/.test(el.id))
      return '#' + escape(el.id);

    // 2. Atributos estáveis
    for (const attr of ['data-testid','data-cy','data-qa','data-id','name','aria-label']) {
      const v = el.getAttribute(attr);
      if (v && v.length < 60) return `[${attr}="${escape(v)}"]`;
    }

    // 3. Classes únicas (ignora classes dinâmicas)
    const badClass = /^(active|hover|focus|selected|disabled|ng-|is-|has-|js-)/;
    if (el.className && typeof el.className === 'string') {
      const cls = el.className.trim().split(/\s+/)
        .filter(c => c && !badClass.test(c))
        .slice(0, 3);
      if (cls.length) {
        const sel = el.tagName.toLowerCase() + '.' + cls.map(escape).join('.');
        try { if (document.querySelectorAll(sel).length === 1) return sel; } catch(e) {}
      }
    }

    // 4. Caminho com nth-of-type
    const tag     = el.tagName.toLowerCase();
    const parent  = el.parentElement;
    if (!parent) return tag;

    const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
    const idx      = siblings.indexOf(el) + 1;
    const part     = siblings.length > 1 ? `${tag}:nth-of-type(${idx})` : tag;
    const parentSel = getSelector(parent);
    return parentSel === 'body' ? part : `${parentSel} > ${part}`;
  }

  /* ── Eventos ────────────────────────────────────── */
  let _lastTarget = null;

  function onMove(e) {
    const t = e.target;
    if (t === hl || t === tip || t === banner) return;
    _lastTarget = t;
    const r = t.getBoundingClientRect();
    hl.style.top    = r.top    + 'px';
    hl.style.left   = r.left   + 'px';
    hl.style.width  = r.width  + 'px';
    hl.style.height = r.height + 'px';
    const sel = getSelector(t);
    window._pyflow_hover_selector = sel;
    tip.textContent = sel;
    const tipTop = r.top - 36 < 40 ? r.bottom + 6 : r.top - 34;
    tip.style.top  = tipTop + 'px';
    tip.style.left = Math.min(r.left, window.innerWidth - 500) + 'px';
  }

  function onClick(e) {
    if (e.target === hl || e.target === tip || e.target === banner) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    window._pyflow_selector = getSelector(e.target);
    _cleanup();
  }

  function onKey(e) {
    if (e.key === 'Escape') {
      window._pyflow_selector = '__cancelled__';
      _cleanup();
    }
  }

  function _cleanup() {
    document.removeEventListener('mouseover', onMove, true);
    document.removeEventListener('click',     onClick, true);
    document.removeEventListener('keydown',   onKey,   true);
    hl.remove(); tip.remove(); banner.remove();
    window._pyflow_picker_active = false;
  }

  document.addEventListener('mouseover', onMove, true);
  document.addEventListener('click',     onClick, true);
  document.addEventListener('keydown',   onKey,   true);

  return 'started';
})();
"""

_POLL_JS   = "return window._pyflow_selector || null;"
_HOVER_JS  = "return window._pyflow_hover_selector || null;"
_CANCEL_JS = """
  window._pyflow_selector = '__cancelled__';
  const hl = document.getElementById('_pyflow_hl');
  const tp = document.getElementById('_pyflow_tip');
  if (hl) hl.remove();
  if (tp) tp.remove();
  window._pyflow_picker_active = false;
"""


# ── Diálogo ───────────────────────────────────────────────────────────────────

class SelectorPickerDialog(QDialog):
    """
    Abre e injeta o overlay de captura de seletor CSS no Chrome ativo.
    Retorna o seletor capturado via self.selected_selector após accept().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📍 Capturar Seletor CSS")
        self.setMinimumWidth(520)
        self.setModal(False)          # não bloqueia — usuário precisa clicar no Chrome
        self.selected_selector = ""
        self._history: list[str] = []
        self._timer = QTimer(self)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._poll)
        self._driver = None
        self._build_ui()
        self._apply_styles()
        self._start_picker()

    # ── Construção da UI ──────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # Título
        title = QLabel("📍  Capturar Seletor CSS")
        title.setObjectName("picker_title")
        root.addWidget(title)

        # Status
        self.lbl_status = QLabel("🔵  Aguardando clique no Chrome...")
        self.lbl_status.setObjectName("picker_status")
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)

        root.addWidget(self._sep())

        # Preview do hover
        lbl_hover = QLabel("Elemento sob o cursor:")
        lbl_hover.setObjectName("picker_label")
        root.addWidget(lbl_hover)

        self.lbl_hover = QLabel("—")
        self.lbl_hover.setObjectName("picker_hover")
        self.lbl_hover.setWordWrap(True)
        root.addWidget(self.lbl_hover)

        root.addWidget(self._sep())

        # Seletor capturado
        lbl_sel = QLabel("Seletor capturado:")
        lbl_sel.setObjectName("picker_label")
        root.addWidget(lbl_sel)

        sel_row = QHBoxLayout()
        self.edit_selector = QLineEdit()
        self.edit_selector.setObjectName("picker_edit")
        self.edit_selector.setPlaceholderText("Clique no Chrome para capturar...")
        self.edit_selector.setReadOnly(False)
        sel_row.addWidget(self.edit_selector, 1)

        btn_copy = QPushButton("⎘")
        btn_copy.setObjectName("btn_copy_small")
        btn_copy.setFixedSize(30, 30)
        btn_copy.setToolTip("Copiar seletor")
        btn_copy.clicked.connect(self._copy)
        sel_row.addWidget(btn_copy)

        root.addLayout(sel_row)

        # Histórico de capturas
        lbl_hist = QLabel("Histórico desta sessão:")
        lbl_hist.setObjectName("picker_label")
        root.addWidget(lbl_hist)

        self.list_history = QListWidget()
        self.list_history.setObjectName("picker_history")
        self.list_history.setMaximumHeight(110)
        self.list_history.itemClicked.connect(
            lambda item: self.edit_selector.setText(item.text())
        )
        root.addWidget(self.list_history)

        root.addWidget(self._sep())

        # Instrução
        instr = QLabel(
            "💡  Passe o mouse pelo Chrome — o elemento fica destacado em azul.\n"
            "Clique para capturar o seletor.  Pressione Esc no Chrome para cancelar."
        )
        instr.setObjectName("picker_hint")
        instr.setWordWrap(True)
        root.addWidget(instr)

        # Botões
        btn_row = QHBoxLayout()

        self.btn_recapture = QPushButton("↺  Capturar novamente")
        self.btn_recapture.setObjectName("btn_recapture")
        self.btn_recapture.clicked.connect(self._start_picker)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self._on_cancel)

        self.btn_insert = QPushButton("✓  Usar este seletor")
        self.btn_insert.setObjectName("btn_insert")
        self.btn_insert.setDefault(True)
        self.btn_insert.clicked.connect(self._on_insert)

        btn_row.addWidget(self.btn_recapture)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_insert)
        root.addLayout(btn_row)

    def _sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("picker_sep")
        return sep

    # ── Lógica de captura ─────────────────────────────────────────────

    def _start_picker(self):
        from blocks.browser.open_browser import OpenBrowserBlock
        self._driver = OpenBrowserBlock.get_driver()

        if not self._driver:
            self.lbl_status.setText("⚠️  Nenhum navegador aberto. Abra o Chrome com o bloco 'Abrir Navegador' primeiro.")
            return

        try:
            result = self._driver.execute_script(_PICKER_JS)
            if result == "already_active":
                pass
            self.lbl_status.setText("🔵  Overlay ativo — clique em qualquer elemento no Chrome")
            self.btn_recapture.setEnabled(False)
            self._timer.start()
        except Exception as e:
            self.lbl_status.setText(f"⚠️  Erro ao injetar overlay: {str(e)[:120]}")

    def _poll(self):
        """Verifica a cada 300ms se o usuário clicou em um elemento."""
        if not self._driver:
            return
        try:
            # Atualiza hover preview
            hover = self._driver.execute_script(_HOVER_JS)
            if hover:
                self.lbl_hover.setText(hover)

            # Verifica se houve clique
            sel = self._driver.execute_script(_POLL_JS)
            if sel:
                self._timer.stop()
                self.btn_recapture.setEnabled(True)

                if sel == "__cancelled__":
                    self.lbl_status.setText("⚪  Cancelado — clique em 'Capturar novamente' para tentar de novo")
                    self.lbl_hover.setText("—")
                    return

                self.edit_selector.setText(sel)
                self.selected_selector = sel
                self.lbl_status.setText(f"✅  Seletor capturado!")
                self.lbl_hover.setText(sel)

                # Adiciona ao histórico se não for duplicata
                if sel not in self._history:
                    self._history.insert(0, sel)
                    item = QListWidgetItem(sel)
                    item.setFont(QFont("Consolas", 10))
                    self.list_history.insertItem(0, item)

        except Exception:
            # Driver pode ter sido fechado
            self._timer.stop()
            self.lbl_status.setText("⚠️  Conexão com o navegador perdida.")

    def _copy(self):
        sel = self.edit_selector.text().strip()
        if sel:
            QApplication.clipboard().setText(sel)

    def _on_cancel(self):
        self._timer.stop()
        if self._driver:
            try:
                self._driver.execute_script(_CANCEL_JS)
            except Exception:
                pass
        self.reject()

    def _on_insert(self):
        self.selected_selector = self.edit_selector.text().strip()
        self._timer.stop()
        self.accept()

    def closeEvent(self, event):
        self._timer.stop()
        if self._driver:
            try:
                self._driver.execute_script(_CANCEL_JS)
            except Exception:
                pass
        super().closeEvent(event)

    # ── Estilos ───────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }

            #picker_title {
                font-size: 16px; font-weight: 700; color: #89b4fa;
            }
            #picker_status {
                font-size: 12px; color: #a6adc8; padding: 6px 10px;
                background: #181825; border-radius: 6px;
                border: 1px solid #313244;
            }
            #picker_label  { font-size: 11px; color: #6c7086; }
            #picker_hover  {
                font-family: Consolas, monospace; font-size: 11px;
                color: #cba6f7; padding: 4px 8px;
                background: #221838; border-radius: 4px;
                border: 1px solid #3a2a55; min-height: 24px;
            }
            #picker_hint   { font-size: 11px; color: #45475a; font-style: italic; }
            #picker_sep    { color: #313244; }

            #picker_edit {
                background-color: #313244; border: 1px solid #89b4fa;
                border-radius: 6px; padding: 8px 10px;
                color: #89b4fa; font-family: Consolas, monospace;
                font-size: 12px; font-weight: 600;
            }
            #picker_edit:focus { border-color: #cba6f7; }

            #picker_history {
                background-color: #181825; border: 1px solid #313244;
                border-radius: 6px; color: #a6adc8; font-size: 11px;
            }
            #picker_history::item { padding: 4px 8px; }
            #picker_history::item:hover     { background: #313244; }
            #picker_history::item:selected  { background: #313244; color: #89b4fa; }

            #btn_copy_small {
                background: #313244; border: 1px solid #45475a;
                border-radius: 6px; color: #6c7086; font-size: 14px;
            }
            #btn_copy_small:hover { color: #89b4fa; border-color: #89b4fa; }

            #btn_recapture {
                background: #1e2a3e; color: #89b4fa;
                border: 1px solid #89b4fa; border-radius: 6px;
                padding: 6px 14px; font-size: 12px;
            }
            #btn_recapture:hover    { background: #263550; }
            #btn_recapture:disabled { color: #45475a; border-color: #45475a; background: #1e1e2e; }

            #btn_insert {
                background: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 7px 20px; font-weight: 700; font-size: 13px;
            }
            #btn_insert:hover { background: #9ec4fa; }

            #btn_cancel {
                background: #313244; color: #cdd6f4;
                border: none; border-radius: 6px;
                padding: 7px 14px; font-size: 13px;
            }
            #btn_cancel:hover { background: #45475a; }
        """)
