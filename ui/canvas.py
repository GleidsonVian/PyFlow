import copy

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel,
    QFrame, QHBoxLayout, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint, QMimeData
from PySide6.QtGui import QPainter, QColor, QPen, QDrag, QPixmap, QCursor

from ui.param_dialog import ParamDialog
from engine.blocks_registry import BLOCK_BY_NAME, ALL_BLOCKS
from blocks.control.sequence_start_block import SequenceStartBlock
from blocks.control.sequence_end_block   import SequenceEndBlock

BLOCK_REGISTRY = BLOCK_BY_NAME

CATEGORY_IDLE_COLORS = {
    "Navegador":   ("#1a2a40", "#89b4fa"),
    "Controle":    ("#201830", "#cba6f7"),
    "Arquivos":    ("#1a2e20", "#a6e3a1"),
    "Integração":  ("#2e2018", "#fab387"),
    "Sistema":     ("#2e1818", "#f38ba8"),
    "Gatilhos":    ("#2e2a18", "#f9e2af"),
}


class CanvasBlockWidget(QFrame):
    clicked      = Signal(object)
    removed      = Signal(object)
    duplicated   = Signal(object)
    move_up      = Signal(object)
    move_down    = Signal(object)
    toggled_collapse = Signal(object)
    run_from     = Signal(object)

    STATE_COLORS = {
        "running": ("#1c3a5e", "#89b4fa"),
        "success": ("#1c3a2a", "#a6e3a1"),
        "error":   ("#3a1c1c", "#f38ba8"),
    }

    def __init__(self, block_instance, params, index):
        super().__init__()
        self.block_instance = block_instance
        self.params = params
        self.index = index
        self.state = "idle"
        self.is_sequence_start = isinstance(self.block_instance, SequenceStartBlock)
        self.is_collapsed = False
        self._drag_start_pos = None
        self._build_ui()
        self._apply_state()
        self._refresh_nota()

    def _get_category(self):
        return getattr(self.block_instance, "category", "Controle")

    def _build_ui(self):
        self.setObjectName("canvas_block")
        self.setMinimumHeight(72)
        self.setCursor(Qt.PointingHandCursor)

        # Layout vertical externo: linha principal + nota (opcional)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Linha principal ───────────────────────────────────────────
        row = QHBoxLayout()
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(10)

        if self.is_sequence_start:
            self.collapse_button = QLabel("▼")
            self.collapse_button.setObjectName("collapse_button")
            self.collapse_button.setFixedSize(22, 22)
            self.collapse_button.setAlignment(Qt.AlignCenter)
            self.collapse_button.setCursor(Qt.PointingHandCursor)
            self.collapse_button.mousePressEvent = self._toggle_collapse
            row.addWidget(self.collapse_button)

        self.drag_handle = QLabel("⠿")
        self.drag_handle.setObjectName("drag_handle")
        self.drag_handle.setFixedWidth(16)
        self.drag_handle.setAlignment(Qt.AlignCenter)
        self.drag_handle.setCursor(Qt.SizeVerCursor)

        self.lbl_index = QLabel(str(self.index + 1))
        self.lbl_index.setObjectName("block_index")
        self.lbl_index.setFixedSize(28, 28)
        self.lbl_index.setAlignment(Qt.AlignCenter)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.lbl_name = QLabel(self.block_instance.name)
        self.lbl_name.setObjectName("block_name")
        params_text = "  ·  ".join(
            f"{k}: {v}" for k, v in self.params.items()
            if k != "nota" and v not in (None, "", False)
        ) or "Sem parâmetros"
        self.lbl_params = QLabel(params_text)
        self.lbl_params.setObjectName("block_params")
        self.lbl_params.setWordWrap(False)
        info.addWidget(self.lbl_name)
        info.addWidget(self.lbl_params)

        self.btn_remove = QLabel("✕")
        self.btn_remove.setObjectName("btn_remove")
        self.btn_remove.setFixedSize(22, 22)
        self.btn_remove.setAlignment(Qt.AlignCenter)
        self.btn_remove.setCursor(Qt.PointingHandCursor)
        self.btn_remove.mousePressEvent = lambda e: self.removed.emit(self)

        row.addWidget(self.drag_handle)
        row.addWidget(self.lbl_index)
        row.addLayout(info, 1)
        row.addWidget(self.btn_remove)
        outer.addLayout(row)

        # ── Nota (linha extra, visível só quando preenchida) ──────────
        self.lbl_nota = QLabel("")
        self.lbl_nota.setObjectName("block_nota")
        self.lbl_nota.setWordWrap(True)
        self.lbl_nota.setContentsMargins(58, 0, 14, 8)   # alinha com o texto acima
        self.lbl_nota.hide()
        outer.addWidget(self.lbl_nota)

    def set_state(self, state):
        self.state = state
        self._apply_state()

    def _toggle_collapse(self, event):
        self.is_collapsed = not self.is_collapsed
        self.collapse_button.setText("▶" if self.is_collapsed else "▼")
        self.toggled_collapse.emit(self)

    def _apply_state(self):
        cat = self._get_category()
        bg, accent = (self.STATE_COLORS.get(self.state)
                      or CATEGORY_IDLE_COLORS.get(cat, ("#313244", "#cba6f7")))
        self.setStyleSheet(f"""
            #canvas_block {{ 
                background-color: {bg}; 
                border: 1px solid {accent}; 
                border-radius: 8px;
            }}
            #drag_handle {{ color: #45475a; font-size: 14px; }}
            #block_index {{ 
                background-color: rgba(0,0,0,0.2); 
                color: {accent}; 
                border-radius: 4px; 
                font-size: 10px; 
                font-weight: 800; 
            }}
            #block_name {{ color: #cdd6f4; font-size: 12px; font-weight: 700; }}
            #block_params {{ color: #9399b2; font-size: 10px; font-family: 'Segoe UI', sans-serif; }}
            #block_nota {{ color: #585b70; font-size: 10px; font-style: italic; }}
            #btn_remove {{ color: #45475a; border-radius: 4px; font-size: 10px; }}
            #btn_remove:hover {{ color: #f38ba8; background-color: rgba(243, 139, 168, 0.1); }}
        """)

    def _set_scope_indicator(self, color: str | None):
        """Adiciona borda esquerda colorida quando o bloco está dentro de um escopo."""
        if color:
            self.setStyleSheet(
                self.styleSheet() +
                f"\n#canvas_block {{ border-left: 4px solid {color}; border-radius: 0 10px 10px 0; }}"
            )

    def update_params_label(self):
        params_text = "  ·  ".join(
            f"{k}: {v}" for k, v in self.params.items()
            if k != "nota" and v not in (None, "", False)
        ) or "Sem parâmetros"
        self.lbl_params.setText(params_text)
        self._refresh_nota()

    def _refresh_nota(self):
        nota = self.params.get("nota", "").strip()
        if nota:
            self.lbl_nota.setText(f"📝  {nota}")
            self.lbl_nota.show()
        else:
            self.lbl_nota.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._drag_start_pos is None:
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance() * 2:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"__reorder__{id(self)}")
        drag.setMimeData(mime)
        pix = QPixmap(self.size())
        pix.fill(QColor(0, 0, 0, 0))
        self.render(pix)
        drag.setPixmap(pix)
        drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.MoveAction)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; padding: 4px; color: #cdd6f4; font-size: 13px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #313244; color: #cba6f7; }
            QMenu::separator { background-color: #313244; height: 1px; margin: 4px 0; }
        """)
        act_run  = menu.addAction("▶  Executar a partir daqui")
        menu.addSeparator()
        act_dup  = menu.addAction("📋  Duplicar bloco")
        menu.addSeparator()
        act_up   = menu.addAction("⬆  Mover para cima")
        act_down = menu.addAction("⬇  Mover para baixo")
        menu.addSeparator()
        act_del  = menu.addAction("✕  Remover bloco")
        action = menu.exec(event.globalPos())
        if action == act_run:    self.run_from.emit(self)
        elif action == act_dup:  self.duplicated.emit(self)
        elif action == act_up:   self.move_up.emit(self)
        elif action == act_down: self.move_down.emit(self)
        elif action == act_del:  self.removed.emit(self)





class ConnectorArrow(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx = self.width() // 2
        painter.setPen(QPen(QColor("#45475a"), 1.5))
        painter.drawLine(cx, 0, cx, self.height() - 8)
        painter.setBrush(QColor("#45475a"))
        painter.setPen(Qt.NoPen)
        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint
        painter.drawPolygon(QPolygon([
            QPoint(cx - 5, self.height() - 8),
            QPoint(cx + 5, self.height() - 8),
            QPoint(cx,     self.height() - 1),
        ]))


class Canvas(QWidget):
    block_selected  = Signal(object)
    canvas_clicked  = Signal()
    block_updated   = Signal()
    run_from_index  = Signal(int)

    _MAX_HISTORY = 60

    def __init__(self):
        super().__init__()
        self.setObjectName("canvas_outer")
        self.setAcceptDrops(True)
        self._blocks: list = []
        self._selected = None
        self._undo_stack: list = []
        self._redo_stack: list = []
        self._build_ui()
        self._apply_styles()
        self.setFocusPolicy(Qt.StrongFocus)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("canvas_scroll")
        self.inner = QWidget()
        self.inner.setObjectName("canvas_inner")
        self.flow_layout = QVBoxLayout(self.inner)
        self.flow_layout.setContentsMargins(80, 40, 80, 40)
        self.flow_layout.setSpacing(0)
        self.flow_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self._empty_label = QLabel("Arraste blocos do painel esquerdo\npara começar seu fluxo")
        self._empty_label.setObjectName("empty_hint")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self.flow_layout.addWidget(self._empty_label)
        self.flow_layout.addStretch(1)
        self.scroll.setWidget(self.inner)
        outer.addWidget(self.scroll)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        if text.startswith("__reorder__"):
            widget = next((b for b in self._blocks if id(b) == int(text[11:])), None)
            if widget:
                drop_pos = self.inner.mapFromGlobal(QCursor.pos())
                self._reorder(widget, self._get_insert_index(drop_pos.y()))
            event.acceptProposedAction()
            return
        block_cls = BLOCK_REGISTRY.get(text)
        if not block_cls: return
        block_instance = block_cls()
        default_params = {s["name"]: s.get("default", "") for s in block_cls.params_schema}
        dialog = ParamDialog(block_instance, default_params, self)
        if dialog.exec():
            self._add_block(block_instance, dialog.get_params())
        event.acceptProposedAction()

    def _get_insert_index(self, y):
        for i, blk in enumerate(self._blocks):
            if y < blk.mapTo(self.inner, QPoint(0, 0)).y() + blk.height() // 2:
                return i
        return len(self._blocks)

    # ── Indentação visual ─────────────────────────────────────────────

    # Cores de borda por tipo de container (nível 1 usará a cor do container mais externo)
    _SCOPE_COLORS = {
        "LoopBlock":     "#fab387",   # laranja
        "ForEachBlock":  "#a6e3a1",   # verde
        "IfBlock":       "#89b4fa",   # azul
        "ElseBlock":     "#f38ba8",   # rosa (ramo else)
        "TryBlock":      "#f9e2af",   # amarelo
        "CatchBlock":    "#f38ba8",   # vermelho (ramo de erro)
        "WhileBlock":    "#94e2d5",   # teal
    }
    _OPEN_TYPES  = frozenset({"LoopBlock", "ForEachBlock", "IfBlock", "TryBlock", "WhileBlock"})
    _CLOSE_TYPES = frozenset({"EndLoopBlock", "EndForEachBlock", "EndIfBlock", "EndTryBlock", "EndWhileBlock"})

    def _compute_indent(self, blocks: list) -> list:
        """
        Retorna lista de (nivel, cor_de_escopo) para cada bloco.
        Nível 0 = sem indentação.
        """
        results    = []
        stack      = []   # pilha de cores do escopo atual

        for blk in blocks:
            btype = type(blk.block_instance).__name__

            if btype in self._CLOSE_TYPES:
                # Fecha escopo — recua ANTES de renderizar este bloco
                if stack:
                    stack.pop()
                color = stack[-1] if stack else None
                results.append((len(stack), color))

            elif btype in ("ElseBlock", "CatchBlock"):
                # Mesmo nível do bloco pai mas muda a cor (ramo alternativo)
                color = self._SCOPE_COLORS.get(btype, "#f38ba8")
                if stack:
                    stack[-1] = color
                results.append((len(stack) - 1 if stack else 0, color))

            elif btype in self._OPEN_TYPES:
                # Renderiza o bloco de abertura no nível atual
                color = self._SCOPE_COLORS.get(btype)
                results.append((len(stack), color))
                stack.append(color)   # abre escopo APÓS renderizar

            else:
                color = stack[-1] if stack else None
                results.append((len(stack), color))

        return results

    def _full_rebuild(self):
        # Limpa o layout, mas mantém os widgets dos blocos vivos
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            w = item.widget()
            if w and w not in self._blocks and w is not self._empty_label:
                w.deleteLater()

        # Reatribui o índice real para todos os blocos
        for i, blk in enumerate(self._blocks):
            blk.index = i

        visible_blocks = [b for b in self._blocks if not b.isHidden()]
        self._empty_label.setVisible(not self._blocks)  # Mostra se não houver blocos
        self.flow_layout.addWidget(self._empty_label)

        # Calcula nível de indentação por bloco
        indent_levels = self._compute_indent(visible_blocks)

        # Adiciona apenas os blocos visíveis e conectores ao layout
        for i, blk in enumerate(visible_blocks):
            blk.lbl_index.setText(str(i + 1))
            blk._apply_state()
            level, scope_color = indent_levels[i]
            blk.setContentsMargins(level * 24, 0, 0, 0)
            blk._set_scope_indicator(scope_color)
            if i > 0:
                arrow = ConnectorArrow()
                arrow.setContentsMargins(level * 24, 0, 0, 0)
                self.flow_layout.addWidget(arrow)
            self.flow_layout.addWidget(blk)

        self.flow_layout.addStretch(1)

    def _append_to_layout(self, widget):
        last = self.flow_layout.count() - 1
        if last >= 0:
            item = self.flow_layout.itemAt(last)
            if item and item.widget() is None:
                self.flow_layout.takeAt(last)
        self._empty_label.setVisible(False)
        if len(self._blocks) > 1:
            self.flow_layout.addWidget(ConnectorArrow())
        self.flow_layout.addWidget(widget)
        self.flow_layout.addStretch(1)

    # ── Undo / Redo ───────────────────────────────────────────────────────

    def _snapshot(self) -> list:
        """Captura o estado atual do canvas como lista serializável."""
        return [
            {"block": type(b.block_instance).__name__, "params": copy.deepcopy(b.params)}
            for b in self._blocks
        ]

    def _push_history(self):
        """Salva o estado atual na pilha de undo e apaga o redo."""
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > self._MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _restore(self, snapshot: list):
        """Restaura o canvas a partir de um snapshot sem gerar novo histórico."""
        self._blocks.clear()
        self._selected = None
        for step in snapshot:
            cls = BLOCK_REGISTRY.get(step["block"])
            if cls:
                widget = CanvasBlockWidget(cls(), copy.deepcopy(step["params"]),
                                           len(self._blocks))
                self._connect_block(widget)
                self._blocks.append(widget)
        self._full_rebuild()
        self.canvas_clicked.emit()
        self.block_updated.emit()

    def undo(self):
        """Desfaz a última ação (Ctrl+Z)."""
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())

    def redo(self):
        """Refaz a última ação desfeita (Ctrl+Y)."""
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.undo(); return
            if event.key() == Qt.Key_Y:
                self.redo(); return
        super().keyPressEvent(event)

    # ── Conexão de sinais do bloco ────────────────────────────────────────

    def _connect_block(self, widget):
        widget.clicked.connect(self._on_block_clicked)
        widget.removed.connect(self._remove_block)
        widget.toggled_collapse.connect(self._on_sequence_toggled)
        widget.duplicated.connect(self._duplicate_block)
        widget.move_up.connect(self._move_up)
        widget.move_down.connect(self._move_down)
        widget.run_from.connect(self._on_run_from)

    def _add_block(self, block_instance, params, insert_at=None):
        self._push_history()
        widget = CanvasBlockWidget(block_instance, params,
                                   insert_at if insert_at is not None else len(self._blocks))
        self._connect_block(widget)
        if insert_at is not None and 0 <= insert_at < len(self._blocks):
            self._blocks.insert(insert_at, widget)
            self._full_rebuild()
        else:
            self._blocks.append(widget)
            self._append_to_layout(widget)
        self._select_block(widget)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _duplicate_block(self, widget):
        # _add_block já chama _push_history internamente
        idx = self._blocks.index(widget) + 1 if widget in self._blocks else len(self._blocks)
        self._add_block(type(widget.block_instance)(), copy.deepcopy(widget.params), insert_at=idx)
        self.block_updated.emit()

    def _move_up(self, widget):
        idx = self._blocks.index(widget) if widget in self._blocks else -1
        if idx > 0:
            self._push_history()
            self._blocks[idx], self._blocks[idx - 1] = self._blocks[idx - 1], self._blocks[idx]
            self._full_rebuild(); self._select_block(widget); self.block_updated.emit()

    def _move_down(self, widget):
        idx = self._blocks.index(widget) if widget in self._blocks else -1
        if 0 <= idx < len(self._blocks) - 1:
            self._push_history()
            self._blocks[idx], self._blocks[idx + 1] = self._blocks[idx + 1], self._blocks[idx]
            self._full_rebuild(); self._select_block(widget); self.block_updated.emit()

    def _reorder(self, widget, new_index):
        if widget not in self._blocks: return
        self._push_history()
        self._blocks.pop(self._blocks.index(widget))
        self._blocks.insert(min(new_index, len(self._blocks)), widget)
        self._full_rebuild(); self._select_block(widget); self.block_updated.emit()

    def _on_sequence_toggled(self, start_widget):
        start_index = self._blocks.index(start_widget)
        is_collapsed = start_widget.is_collapsed

        # Encontra o bloco final correspondente, lidando com aninhamento
        nesting_level = 0
        end_index = -1
        for i in range(start_index + 1, len(self._blocks)):
            block = self._blocks[i]
            if isinstance(block.block_instance, SequenceStartBlock):
                nesting_level += 1
            elif isinstance(block.block_instance, SequenceEndBlock):
                if nesting_level == 0:
                    end_index = i
                    break
                else:
                    nesting_level -= 1

        if end_index != -1:
            # Alterna a visibilidade dos blocos entre o início e o fim
            for i in range(start_index + 1, end_index + 1):
                self._blocks[i].setVisible(not is_collapsed)
        self._full_rebuild()
        self.block_updated.emit()

    def _on_run_from(self, widget):
        if widget in self._blocks:
            self.run_from_index.emit(self._blocks.index(widget))

    def _on_block_clicked(self, widget): self._select_block(widget)

    def _select_block(self, widget):
        self._selected = widget
        self.block_selected.emit(widget)

    def _remove_block(self, widget):
        self._push_history()
        if widget in self._blocks: self._blocks.remove(widget)
        self._full_rebuild()
        if self._selected == widget:
            self._selected = None
            self.canvas_clicked.emit()
        self.block_updated.emit()

    def mousePressEvent(self, event):
        child = self.inner.childAt(self.inner.mapFromGlobal(event.globalPosition().toPoint()))
        if child is None:
            self._selected = None
            self.canvas_clicked.emit()
        super().mousePressEvent(event)

    def set_block_state(self, index, state):
        if 0 <= index < len(self._blocks):
            try: self._blocks[index].set_state(state)
            except RuntimeError: pass

    def reset_block_states(self):
        valid = []
        for b in self._blocks:
            try: b.set_state("idle"); valid.append(b)
            except RuntimeError: pass
        self._blocks = valid

    def get_selected_block(self): return self._selected
    def get_steps(self): return [{"block_instance": b.block_instance, "params": b.params} for b in self._blocks]
    def get_serialized_steps(self): return [{"block": type(b.block_instance).__name__, "params": b.params} for b in self._blocks]

    def load_from_data(self, steps):
        self.clear_canvas()
        for step in steps:
            cls = BLOCK_REGISTRY.get(step.get("block"))
            if cls: self._add_block(cls(), step.get("params", {}))

    def clear_canvas(self):
        if self._blocks:
            self._push_history()
        self._blocks.clear(); self._selected = None; self._full_rebuild()

    def _apply_styles(self):
        self.setStyleSheet("""
            #canvas_outer { background-color: #11111b; }
            #canvas_scroll { background-color: transparent; border: none; }
            #canvas_inner { background-color: transparent; }
            #empty_hint { color: #45475a; font-size: 15px; padding: 60px 20px; }
        """)

    def paintEvent(self, event):
        """Desenha o grid de fundo estilo n8n/UiPath."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Cor do fundo
        painter.fillRect(self.rect(), QColor("#11111b"))
        
        # Desenha grid
        pen = QPen(QColor("#1e1e2e"), 1)
        painter.setPen(pen)
        
        grid_size = 20
        # Linhas verticais
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        # Linhas horizontais
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
            
        # Linhas de destaque (opcional, estilo n8n)
        pen_bold = QPen(QColor("#181825"), 1)
        painter.setPen(pen_bold)
        for x in range(0, self.width(), grid_size * 5):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size * 5):
            painter.drawLine(0, y, self.width(), y)