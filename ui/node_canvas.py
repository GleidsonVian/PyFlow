"""
Canvas de nós estilo n8n para PyFlow RPA.
Cada nó tem duas saídas: ✅ Sucesso e ❌ Erro.
API pública idêntica à Canvas original para compatibilidade com main_window.
"""

import copy
import math
import uuid

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsObject, QGraphicsItem, QGraphicsPathItem,
    QMenu, QApplication,
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath,
    QFont, QFontMetrics, QTransform,
)

from engine.blocks_registry import BLOCK_BY_NAME
from ui.param_dialog import ParamDialog

BLOCK_REGISTRY = BLOCK_BY_NAME

CATEGORY_COLORS = {
    "Navegador":  ("#1a2a40", "#89b4fa"),
    "Controle":   ("#201830", "#cba6f7"),
    "Arquivos":   ("#1a2e20", "#a6e3a1"),
    "Integração": ("#2e2018", "#fab387"),
    "Sistema":    ("#2e1818", "#f38ba8"),
    "Gatilhos":   ("#2e2a18", "#f9e2af"),
}

STATE_OVERRIDES = {
    "running": ("#1c3a5e", "#89b4fa"),
    "success": ("#1c3a2a", "#a6e3a1"),
    "error":   ("#3a1c1c", "#f38ba8"),
}

NODE_W      = 224
NODE_H      = 78
PORT_R      = 7
PIN_PANEL_H = 56

# ─────────────────────────────────────────────────────────────────────────────
# Port
# ─────────────────────────────────────────────────────────────────────────────

PORT_COLORS = {
    "input":   "#8b8fa8",
    "success": "#a6e3a1",
    "error":   "#f38ba8",
}

class PortItem(QGraphicsItem):
    def __init__(self, port_type: str, node: "NodeItem"):
        super().__init__(node)
        self.port_type = port_type   # "input" | "success" | "error"
        self.node      = node
        self.conns: list["ConnectionItem"] = []
        self.setAcceptHoverEvents(True)
        self.setZValue(3)
        self._hov = False

    @property
    def is_output(self):
        return self.port_type in ("success", "error")

    def boundingRect(self) -> QRectF:
        return QRectF(-PORT_R, -PORT_R, PORT_R * 2, PORT_R * 2)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        col = QColor(PORT_COLORS.get(self.port_type, "#8b8fa8"))
        if self._hov or self.conns:
            painter.setPen(QPen(col, 1.5))
            painter.setBrush(col)
        else:
            painter.setPen(QPen(col.darker(130), 1.5))
            painter.setBrush(QColor("#1e1e2e"))
        painter.drawEllipse(self.boundingRect())

    def scene_center(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))

    def hoverEnterEvent(self, e):
        self._hov = True
        self.update()
        self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self._hov = False
        self.update()
        self.unsetCursor()
        super().hoverLeaveEvent(e)


# ─────────────────────────────────────────────────────────────────────────────
# Connection arrow (bezier)
# ─────────────────────────────────────────────────────────────────────────────

CONN_COLORS = {
    "success": "#a6e3a1",
    "error":   "#f38ba8",
    "input":   "#8b8fa8",
    None:      "#8b8fa8",
}

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, src: PortItem, dst: "PortItem | None" = None):
        super().__init__()
        self.src = src
        self.dst = dst
        self._tip: QPointF | None = None

        if src:
            src.conns.append(self)
        if dst:
            dst.conns.append(self)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(-1)
        self._redraw()

    def _color(self) -> str:
        if self.src:
            return CONN_COLORS.get(self.src.port_type, "#8b8fa8")
        return "#8b8fa8"

    def set_tip(self, pos: QPointF):
        self._tip = pos
        self._redraw()

    def refresh(self):
        self._redraw()

    def _redraw(self):
        if not self.src:
            return
        p0 = self.src.scene_center()
        p1 = self.dst.scene_center() if self.dst else (self._tip or p0)

        dx   = max(abs(p1.x() - p0.x()) * 0.55, 80.0)
        path = QPainterPath(p0)
        path.cubicTo(
            QPointF(p0.x() + dx, p0.y()),
            QPointF(p1.x() - dx, p1.y()),
            p1,
        )
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        base  = self._color()
        col   = "#f38ba8" if self.isSelected() else base
        width = 2.5 if self.isSelected() else 2.0
        pen   = QPen(QColor(col), width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

        if self.dst:
            p1   = self.dst.scene_center()
            p0   = self.src.scene_center()
            dx   = max(abs(p1.x() - p0.x()) * 0.55, 80.0)
            tang = QPointF(p1.x() - dx, p1.y())
            ang  = math.atan2(p1.y() - tang.y(), p1.x() - tang.x())
            sz   = 9
            a1   = ang + math.pi * 0.78
            a2   = ang - math.pi * 0.78
            arr  = QPainterPath(p1)
            arr.lineTo(p1.x() + sz * math.cos(a1), p1.y() + sz * math.sin(a1))
            arr.lineTo(p1.x() + sz * math.cos(a2), p1.y() + sz * math.sin(a2))
            arr.closeSubpath()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(col))
            painter.drawPath(arr)

    def detach(self):
        if self.src and self in self.src.conns:
            self.src.conns.remove(self)
        if self.dst and self in self.dst.conns:
            self.dst.conns.remove(self)
        self.src = None
        self.dst = None


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────

class NodeItem(QGraphicsObject):
    def __init__(self, block_instance, params: dict, node_id: str = ""):
        super().__init__()
        self.block_instance = block_instance
        self.params         = params
        self.node_id        = node_id or uuid.uuid4().hex[:8]
        self.state          = "idle"
        self._idx           = 0

        self._pinned      = False
        self._last_result = ""
        self._last_ok     = True

        self.setFlag(QGraphicsItem.ItemIsMovable,            True)
        self.setFlag(QGraphicsItem.ItemIsSelectable,         True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self._hov = False

        # Três portas: 1 entrada (esquerda), 2 saídas (direita)
        self.in_port      = PortItem("input",   self)
        self.success_port = PortItem("success", self)
        self.error_port   = PortItem("error",   self)
        self._reposition_ports()

    # ── altura ────────────────────────────────────────────────────────────────

    def _total_h(self) -> int:
        return NODE_H + (PIN_PANEL_H if self._pinned else 0)

    def _reposition_ports(self):
        mid = NODE_H // 2
        self.in_port.setPos(0, mid)
        # Portas de saída: ✅ acima do centro, ❌ abaixo
        self.success_port.setPos(NODE_W, int(NODE_H * 0.32))
        self.error_port.setPos(  NODE_W, int(NODE_H * 0.72))

    # ── aparência ─────────────────────────────────────────────────────────────

    def _colors(self) -> tuple[str, str]:
        if self.state in STATE_OVERRIDES:
            return STATE_OVERRIDES[self.state]
        cat = getattr(self.block_instance, "category", "Controle")
        return CATEGORY_COLORS.get(cat, ("#313244", "#cba6f7"))

    def set_state(self, state: str):
        self.state = state
        self.update()

    def set_result(self, message: str, ok: bool):
        self._last_result = message
        self._last_ok     = ok

    def toggle_pin(self):
        self.prepareGeometryChange()
        self._pinned = not self._pinned
        self._reposition_ports()
        self.update()
        for c in list(self.in_port.conns) + list(self.success_port.conns) + list(self.error_port.conns):
            c.refresh()

    def update_params_label(self):
        self.update()

    # ── QGraphicsItem ──────────────────────────────────────────────────────────

    def boundingRect(self) -> QRectF:
        h = self._total_h()
        return QRectF(-PORT_R, -4, NODE_W + PORT_R * 2, h + 8)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        bg, accent = self._colors()
        color = QColor(accent)
        rect  = QRectF(0, 0, NODE_W, NODE_H)

        # Sombra
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(rect.translated(3, 3), 10, 10)

        # Fundo
        painter.setBrush(QColor(bg))
        bw = 2 if (self.isSelected() or self._hov) else 1
        painter.setPen(QPen(color, bw))
        painter.drawRoundedRect(rect, 10, 10)

        # Barra de cor no topo
        clip = QPainterPath()
        clip.addRoundedRect(rect, 10, 10)
        painter.setClipPath(clip)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(QRectF(0, 0, NODE_W, 5))
        painter.setClipping(False)

        # Ícone categoria
        cat_icons = {
            "Navegador": "🌐", "Controle": "🔧", "Arquivos": "📁",
            "Integração": "🔌", "Sistema": "💻", "Gatilhos": "⚡",
        }
        cat  = getattr(self.block_instance, "category", "")
        icon = cat_icons.get(cat, "•")
        painter.setPen(QColor(accent))
        painter.setFont(QFont("Segoe UI Emoji", 11))
        painter.drawText(QRectF(10, 9, 22, 22), Qt.AlignCenter, icon)

        # Badge índice
        badge = QRectF(NODE_W - 30, 9, 26, 16)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 70))
        painter.drawRoundedRect(badge, 3, 3)
        painter.setPen(color)
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(badge, Qt.AlignCenter, str(self._idx + 1))

        # Nome
        painter.setPen(QColor("#cdd6f4"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(36, 9, NODE_W - 70, 22),
                         Qt.AlignVCenter | Qt.AlignLeft, self.block_instance.name)

        # Parâmetros
        painter.setPen(QColor("#9399b2"))
        font_p = QFont("Segoe UI", 9)
        painter.setFont(font_p)
        pts = "  ·  ".join(
            f"{k}: {str(v)[:24]}"
            for k, v in self.params.items()
            if k not in ("nota",) and v not in (None, "", False)
        ) or "Sem parâmetros"
        elided = QFontMetrics(font_p).elidedText(pts, Qt.ElideRight, NODE_W - 30)
        painter.drawText(QRectF(12, 36, NODE_W - 24, 20), Qt.AlignVCenter | Qt.AlignLeft, elided)

        # Nota
        nota = self.params.get("nota", "").strip()
        if nota:
            painter.setPen(QColor("#585b70"))
            font_n = QFont("Segoe UI", 8)
            painter.setFont(font_n)
            nota_e = QFontMetrics(font_n).elidedText(f"📝 {nota}", Qt.ElideRight, NODE_W - 30)
            painter.drawText(QRectF(12, 58, NODE_W - 24, 14), Qt.AlignVCenter | Qt.AlignLeft, nota_e)

        # Labels das portas de saída (✓ e ✗)
        sy = int(NODE_H * 0.32)
        ey = int(NODE_H * 0.72)
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor("#a6e3a1"))
        painter.drawText(QRectF(NODE_W - 18, sy - 7, 14, 14), Qt.AlignCenter, "✓")
        painter.setPen(QColor("#f38ba8"))
        painter.drawText(QRectF(NODE_W - 18, ey - 7, 14, 14), Qt.AlignCenter, "✗")

        # Painel de output fixado
        if self._pinned:
            py = NODE_H
            ph = PIN_PANEL_H
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#0d0d18"))
            full_clip = QPainterPath()
            full_clip.addRoundedRect(QRectF(0, 0, NODE_W, py + ph), 10, 10)
            painter.setClipPath(full_clip)
            painter.drawRect(QRectF(0, py, NODE_W, ph))
            painter.setClipping(False)

            pin_col = "#a6e3a1" if self._last_ok else "#f38ba8"
            painter.setPen(QPen(QColor(pin_col), 1))
            painter.drawLine(QPointF(0, py), QPointF(NODE_W, py))

            painter.setPen(QColor(pin_col))
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.drawText(QRectF(10, py + 4, 60, 12), Qt.AlignVCenter | Qt.AlignLeft, "OUTPUT")

            painter.setFont(QFont("Segoe UI Emoji", 9))
            painter.drawText(QRectF(NODE_W - 20, py + 3, 16, 14), Qt.AlignCenter, "📌")

            if self._last_result:
                painter.setPen(QColor("#cdd6f4"))
                painter.setFont(QFont("Consolas", 8))
                fm  = QFontMetrics(QFont("Consolas", 8))
                txt = fm.elidedText(self._last_result.replace("\n", " "), Qt.ElideRight, int(NODE_W - 22))
                painter.drawText(QRectF(10, py + 18, NODE_W - 20, ph - 22),
                                 Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, txt)
            else:
                painter.setPen(QColor("#45475a"))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(QRectF(10, py + 18, NODE_W - 20, ph - 22),
                                 Qt.AlignTop | Qt.AlignLeft,
                                 "Sem resultado (execute primeiro)")

    # ── eventos ───────────────────────────────────────────────────────────────

    def hoverEnterEvent(self, e):
        self._hov = True;  self.update(); super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self._hov = False; self.update(); super().hoverLeaveEvent(e)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            grid = 24
            return QPointF(
                round(value.x() / grid) * grid,
                round(value.y() / grid) * grid,
            )
        if change == QGraphicsItem.ItemPositionHasChanged:
            all_ports = [self.in_port, self.success_port, self.error_port]
            for port in all_ports:
                for c in list(port.conns):
                    c.refresh()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, e):
        if self.scene():
            self.scene().sig_edit_node.emit(self)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e):
        sc = self.scene()
        if not sc:
            return
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background:#1e1e2e; border:1px solid #313244;
                    border-radius:6px; padding:4px; color:#cdd6f4; font-size:13px; }
            QMenu::item { padding:6px 20px; border-radius:4px; }
            QMenu::item:selected { background:#313244; color:#cba6f7; }
            QMenu::separator { background:#313244; height:1px; margin:4px 0; }
        """)
        a_edit = menu.addAction("✏  Editar parâmetros")
        a_run  = menu.addAction("▶  Executar a partir daqui")
        menu.addSeparator()
        pin_label = "📌  Desfixar output" if self._pinned else "📌  Fixar output"
        a_pin  = menu.addAction(pin_label)
        menu.addSeparator()
        a_dup  = menu.addAction("📋  Duplicar nó")
        menu.addSeparator()
        a_del  = menu.addAction("✕  Remover nó")

        action = menu.exec(e.screenPos())
        if action == a_edit:
            sc.sig_edit_node.emit(self)
        elif action == a_run:
            sc.sig_run_from_node.emit(self)
        elif action == a_pin:
            self.toggle_pin()
        elif action == a_dup:
            sc.duplicate_node(self)
        elif action == a_del:
            sc.remove_node(self)


# ─────────────────────────────────────────────────────────────────────────────
# Scene
# ─────────────────────────────────────────────────────────────────────────────

class NodeScene(QGraphicsScene):
    sig_node_selected  = Signal(object)
    sig_nodes_changed  = Signal()
    sig_edit_node      = Signal(object)
    sig_run_from_node  = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nodes: list[NodeItem]        = []
        self._conns: list[ConnectionItem]  = []
        self._temp:  ConnectionItem | None = None
        self._src:   PortItem | None       = None
        self.selectionChanged.connect(self._on_sel_changed)

    # ── nó ────────────────────────────────────────────────────────────────────

    def add_node(self, node: NodeItem, pos: QPointF = QPointF(80, 200)) -> NodeItem:
        node.setPos(pos)
        self._nodes.append(node)
        self.addItem(node)
        self._reindex()
        return node

    def remove_node(self, node: NodeItem):
        all_ports = [node.in_port, node.success_port, node.error_port]
        for port in all_ports:
            for c in list(port.conns):
                self._del_conn(c)
        if node in self._nodes:
            self._nodes.remove(node)
        if node.scene():
            self.removeItem(node)
        self._reindex()
        self.sig_nodes_changed.emit()
        self.sig_node_selected.emit(None)

    def duplicate_node(self, node: NodeItem) -> NodeItem:
        new_n = NodeItem(type(node.block_instance)(), copy.deepcopy(node.params))
        self.add_node(new_n, node.pos() + QPointF(48, 48))
        self.sig_nodes_changed.emit()
        return new_n

    # ── conexão ───────────────────────────────────────────────────────────────

    def _del_conn(self, conn: ConnectionItem):
        conn.detach()
        if conn in self._conns:
            self._conns.remove(conn)
        if conn.scene():
            self.removeItem(conn)

    def _make_conn(self, src: PortItem, dst: PortItem) -> "ConnectionItem | None":
        # Evita duplicata exata
        if any(c.src is src and c.dst is dst for c in self._conns):
            return None
        conn = ConnectionItem(src, dst)
        self._conns.append(conn)
        self.addItem(conn)
        self._reindex()
        return conn

    # ── eventos de mouse ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, PortItem) and item.is_output:
                self._src  = item
                self._temp = ConnectionItem(item)
                self.addItem(self._temp)
                self._temp.set_tip(event.scenePos())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._temp:
            self._temp.set_tip(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._temp:
            item = self.itemAt(event.scenePos(), QTransform())
            if (
                isinstance(item, PortItem)
                and not item.is_output
                and item.node is not self._src.node
            ):
                self._temp.detach()
                self.removeItem(self._temp)
                self._make_conn(self._src, item)
                self.sig_nodes_changed.emit()
            else:
                self._temp.detach()
                self.removeItem(self._temp)
            self._temp = None
            self._src  = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── seleção ───────────────────────────────────────────────────────────────

    def _on_sel_changed(self):
        nodes = [i for i in self.selectedItems() if isinstance(i, NodeItem)]
        if nodes:
            self.sig_node_selected.emit(nodes[0])
        elif not any(isinstance(i, ConnectionItem) for i in self.selectedItems()):
            self.sig_node_selected.emit(None)

    # ── ordem de execução ─────────────────────────────────────────────────────

    def _ordered_nodes(self) -> list[NodeItem]:
        """Ordem topológica seguindo conexões de sucesso (para exibição de índices)."""
        success_next: dict[NodeItem, NodeItem] = {}
        has_in: set[NodeItem] = set()

        for c in self._conns:
            if c.src and c.dst:
                if c.src.port_type == "success":
                    success_next[c.src.node] = c.dst.node
                has_in.add(c.dst.node)

        roots = sorted(
            [n for n in self._nodes if n not in has_in],
            key=lambda n: (n.pos().y(), n.pos().x()),
        )

        ordered: list[NodeItem] = []
        visited: set[NodeItem]  = set()

        def visit(node: NodeItem):
            if node in visited:
                return
            visited.add(node)
            ordered.append(node)
            if node in success_next:
                visit(success_next[node])

        for r in roots:
            visit(r)

        for n in self._nodes:
            if n not in visited:
                ordered.append(n)

        return ordered

    def _reindex(self):
        for i, n in enumerate(self._ordered_nodes()):
            n._idx = i
            n.update()

    # ── serialização ──────────────────────────────────────────────────────────

    def get_serialized_steps(self) -> list:
        ordered = self._ordered_nodes()

        # Mapeia node_id → {success: id, error: id}
        routing: dict[str, dict] = {}
        for c in self._conns:
            if c.src and c.dst:
                nid = c.src.node.node_id
                if nid not in routing:
                    routing[nid] = {}
                if c.src.port_type == "success":
                    routing[nid]["success"] = c.dst.node.node_id
                elif c.src.port_type == "error":
                    routing[nid]["error"] = c.dst.node.node_id

        result = []
        for node in ordered:
            step: dict = {
                "block":  type(node.block_instance).__name__,
                "params": copy.deepcopy(node.params),
                "_x":     round(node.pos().x(), 1),
                "_y":     round(node.pos().y(), 1),
                "_id":    node.node_id,
            }
            r = routing.get(node.node_id, {})
            if r.get("success"):
                step["_next_success"] = r["success"]
            if r.get("error"):
                step["_next_error"] = r["error"]
            result.append(step)
        return result

    def load_from_steps(self, steps: list):
        for c in list(self._conns):
            c.detach()
            if c.scene():
                self.removeItem(c)
        for n in list(self._nodes):
            if n.scene():
                self.removeItem(n)
        self._conns.clear()
        self._nodes.clear()
        self._temp = None
        self._src  = None

        if not steps:
            return

        has_pos   = any("_x" in s for s in steps)
        node_map: dict[str, NodeItem] = {}

        for i, step in enumerate(steps):
            cls = BLOCK_REGISTRY.get(step.get("block"))
            if not cls:
                continue
            params  = {k: v for k, v in step.get("params", {}).items()
                       if not k.startswith("_")}
            nid     = step.get("_id") or uuid.uuid4().hex[:8]
            node    = NodeItem(cls(), params, nid)

            if has_pos:
                x = float(step.get("_x", i * (NODE_W + 80)))
                y = float(step.get("_y", 200))
            else:
                x = 80 + i * (NODE_W + 80)
                y = 200

            self.add_node(node, QPointF(x, y))
            node_map[nid] = node

        # Restaura conexões
        has_new  = any("_next_success" in s or "_next_error" in s for s in steps)
        has_old  = any("_next" in s for s in steps)

        if has_new or has_old:
            for step in steps:
                sid = step.get("_id")
                if not sid or sid not in node_map:
                    continue
                src_node = node_map[sid]

                # Novo formato
                nxt_s = step.get("_next_success")
                nxt_e = step.get("_next_error")
                # Retrocompatibilidade com _next (tratado como success)
                nxt_old = step.get("_next")
                if not nxt_s and nxt_old:
                    nxt_s = nxt_old

                if nxt_s and nxt_s in node_map:
                    conn = ConnectionItem(src_node.success_port, node_map[nxt_s].in_port)
                    self._conns.append(conn)
                    self.addItem(conn)
                if nxt_e and nxt_e in node_map:
                    conn = ConnectionItem(src_node.error_port, node_map[nxt_e].in_port)
                    self._conns.append(conn)
                    self.addItem(conn)
        else:
            # Auto-conecta sequencialmente por success
            for i in range(len(self._nodes) - 1):
                conn = ConnectionItem(self._nodes[i].success_port, self._nodes[i + 1].in_port)
                self._conns.append(conn)
                self.addItem(conn)

        self._reindex()

    def get_graph(self) -> list:
        """
        Retorna grafo completo para o runner graph-aware.
        Cada item: {id, block_instance, params, next_success, next_error, _index}
        """
        ordered = self._ordered_nodes()

        routing: dict[str, dict] = {}
        for c in self._conns:
            if c.src and c.dst:
                nid = c.src.node.node_id
                if nid not in routing:
                    routing[nid] = {}
                if c.src.port_type == "success":
                    routing[nid]["success"] = c.dst.node.node_id
                elif c.src.port_type == "error":
                    routing[nid]["error"] = c.dst.node.node_id

        result = []
        for i, node in enumerate(ordered):
            r = routing.get(node.node_id, {})
            result.append({
                "id":            node.node_id,
                "block_instance": node.block_instance,
                "params":         node.params,
                "next_success":   r.get("success"),
                "next_error":     r.get("error"),
                "_index":         i,
            })
        return result


# ─────────────────────────────────────────────────────────────────────────────
# View (pan + zoom)
# ─────────────────────────────────────────────────────────────────────────────

class _NodeView(QGraphicsView):
    def __init__(self, scene: NodeScene, canvas: "NodeCanvas"):
        super().__init__(scene, canvas)
        self._canvas = canvas
        self.setObjectName("node_view")
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSceneRect(-8000, -5000, 16000, 10000)
        self.setBackgroundBrush(QColor("#0d0d18"))
        self.setAcceptDrops(True)

        self._panning   = False
        self._pan_start = QPointF()
        self._zoom      = 1.0

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        grid  = 24
        thick = 5
        l = int(rect.left())   - (int(rect.left())   % grid) - grid
        t = int(rect.top())    - (int(rect.top())    % grid) - grid
        r = int(rect.right())  + grid
        b = int(rect.bottom()) + grid
        thin, bold = [], []
        for x in range(l, r + 1, grid):
            (bold if x % (grid * thick) == 0 else thin).append((x, t, x, b))
        for y in range(t, b + 1, grid):
            (bold if y % (grid * thick) == 0 else thin).append((l, y, r, y))
        painter.setPen(QPen(QColor("#181828"), 1))
        for ln in thin:
            painter.drawLine(*ln)
        painter.setPen(QPen(QColor("#20203a"), 1))
        for ln in bold:
            painter.drawLine(*ln)

    def wheelEvent(self, e):
        factor   = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = self._zoom * factor
        if 0.15 <= new_zoom <= 4.0:
            self._zoom = new_zoom
            self.scale(factor, factor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._start_pan(e.position()); e.accept(); return
        super().mousePressEvent(e)

    def _start_pan(self, pos):
        self._panning = True; self._pan_start = pos
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._panning:
            d = e.position() - self._pan_start
            self._pan_start = e.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(d.x()))
            self.verticalScrollBar().setValue(  self.verticalScrollBar().value()   - int(d.y()))
            e.accept(); return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._panning:
            self._panning = False; self.setCursor(Qt.ArrowCursor); e.accept(); return
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        sc = self.scene()

        # Del / Backspace — apaga selecionados
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for item in list(sc.selectedItems()):
                if isinstance(item, NodeItem):
                    sc.remove_node(item)
                elif isinstance(item, ConnectionItem):
                    sc._del_conn(item)
                    sc.sig_nodes_changed.emit()
            e.accept(); return

        # Ctrl+D — duplica nós selecionados
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_D:
            selected = [i for i in sc.selectedItems() if isinstance(i, NodeItem)]
            if selected:
                self._canvas._push_history()
                sc.clearSelection()
                for node in selected:
                    new_n = sc.duplicate_node(node)
                    if new_n:
                        new_n.setSelected(True)
            e.accept(); return

        super().keyPressEvent(e)

    def dragEnterEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()
        else: e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()
        else: e.ignore()

    def dropEvent(self, e):
        text = e.mimeData().text()
        if text.startswith("__reorder__"):
            e.acceptProposedAction(); return
        block_cls = BLOCK_REGISTRY.get(text)
        if not block_cls:
            e.ignore(); return
        block_inst     = block_cls()
        default_params = {s["name"]: s.get("default", "") for s in block_cls.params_schema}
        dialog = ParamDialog(block_inst, default_params, self._canvas)
        if dialog.exec():
            self._canvas._push_history()
            scene_pos = self.mapToScene(e.position().toPoint())
            node = NodeItem(block_inst, dialog.get_params())
            self.scene().add_node(node, scene_pos)
            self._canvas._auto_connect(node)
            self._canvas._select_node(node)
            self._canvas.block_updated.emit()
        e.acceptProposedAction()


# ─────────────────────────────────────────────────────────────────────────────
# NodeCanvas — API pública idêntica a Canvas
# ─────────────────────────────────────────────────────────────────────────────

class NodeCanvas(QWidget):
    block_selected  = Signal(object)
    canvas_clicked  = Signal()
    block_updated   = Signal()
    run_from_index  = Signal(int)

    _MAX_HISTORY = 60

    def __init__(self):
        super().__init__()
        self.setObjectName("node_canvas_outer")
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._undo_stack: list = []
        self._redo_stack: list = []
        self._selected: NodeItem | None = None
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scene = NodeScene()
        self.view  = _NodeView(self.scene, canvas=self)
        self.scene.sig_node_selected.connect(self._on_node_selected)
        self.scene.sig_nodes_changed.connect(self._on_nodes_changed)
        self.scene.sig_edit_node.connect(self._on_edit_node)
        self.scene.sig_run_from_node.connect(self._on_run_from_node)
        layout.addWidget(self.view)

    def _apply_styles(self):
        self.setStyleSheet("""
            #node_canvas_outer { background: #0d0d18; }
            #node_view { background: transparent; border: none; }
            QRubberBand {
                border: 1px solid #cba6f7;
                background: rgba(203, 166, 247, 28);
            }
        """)

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _push_history(self):
        snap = self.scene.get_serialized_steps()
        self._undo_stack.append(snap)
        if len(self._undo_stack) > self._MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack: return
        self._redo_stack.append(self.scene.get_serialized_steps())
        self.scene.load_from_steps(self._undo_stack.pop())
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()

    def redo(self):
        if not self._redo_stack: return
        self._undo_stack.append(self.scene.get_serialized_steps())
        self.scene.load_from_steps(self._redo_stack.pop())
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()

    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier:
            if e.key() == Qt.Key_Z: self.undo(); return
            if e.key() == Qt.Key_Y: self.redo(); return
        super().keyPressEvent(e)

    # ── API pública ───────────────────────────────────────────────────────────

    def set_block_state(self, index: int, state: str):
        ordered = self.scene._ordered_nodes()
        if 0 <= index < len(ordered):
            try: ordered[index].set_state(state)
            except RuntimeError: pass

    def set_block_result(self, index: int, message: str, ok: bool = True):
        ordered = self.scene._ordered_nodes()
        if 0 <= index < len(ordered):
            try: ordered[index].set_result(message, ok)
            except RuntimeError: pass

    def reset_block_states(self):
        for n in list(self.scene._nodes):
            try: n.set_state("idle")
            except RuntimeError: pass

    def get_selected_block(self) -> "NodeItem | None":
        return self._selected

    def get_steps(self) -> list:
        return [{"block_instance": n.block_instance, "params": n.params}
                for n in self.scene._ordered_nodes()]

    def get_serialized_steps(self) -> list:
        return self.scene.get_serialized_steps()

    def get_graph(self) -> list:
        """Retorna grafo completo para execução condicional (runner graph-aware)."""
        return self.scene.get_graph()

    def load_from_data(self, steps: list):
        self._push_history()
        self.scene.load_from_steps(steps)
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()

    def clear_canvas(self):
        if self.scene._nodes: self._push_history()
        self.scene.load_from_steps([])
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()

    def _add_block(self, block_instance, params, **_kwargs):
        self._push_history()
        node  = NodeItem(block_instance, params)
        nodes = self.scene._nodes
        pos   = nodes[-1].pos() + QPointF(NODE_W + 80, 0) if nodes else QPointF(80, 200)
        self.scene.add_node(node, pos)
        self._auto_connect(node)
        self._select_node(node)
        self.block_updated.emit()

    def _auto_connect(self, new_node: NodeItem):
        nodes = self.scene._nodes
        if len(nodes) < 2: return
        prev = nodes[-2]
        if not prev.success_port.conns:
            conn = ConnectionItem(prev.success_port, new_node.in_port)
            self.scene._conns.append(conn)
            self.scene.addItem(conn)
            self.scene._reindex()

    # Drop é tratado em _NodeView
    def dragEnterEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()

    def dragMoveEvent(self, e): e.acceptProposedAction()

    def _on_node_selected(self, node):
        self._selected = node
        if node: self.block_selected.emit(node)
        else:    self.canvas_clicked.emit()

    def _on_nodes_changed(self):
        self.block_updated.emit()

    def _select_node(self, node: NodeItem):
        self.scene.clearSelection()
        node.setSelected(True)
        self._selected = node
        self.block_selected.emit(node)

    def _on_edit_node(self, node: NodeItem):
        dialog = ParamDialog(node.block_instance, node.params, self)
        if dialog.exec():
            self._push_history()
            node.params = dialog.get_params()
            node.update_params_label()
            self.block_updated.emit()
            self.block_selected.emit(node)

    def _on_run_from_node(self, node: NodeItem):
        ordered = self.scene._ordered_nodes()
        if node in ordered:
            self.run_from_index.emit(ordered.index(node))

    def fit_all(self):
        if self.scene._nodes:
            self.view.fitInView(
                self.scene.itemsBoundingRect().adjusted(-60, -60, 60, 60),
                Qt.KeepAspectRatio)
