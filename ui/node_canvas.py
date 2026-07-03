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
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath,
    QFont, QFontMetrics, QTransform,
)

from engine.blocks_registry import BLOCK_BY_NAME
from ui.node_details_dialog import NodeDetailsDialog
from ui.param_dialog import ParamDialog
from ui.comment_item import CommentItem
from ui.minimap import Minimap
from ui.data_viewer import DataViewerDialog
from ui.connection_style import (
    SNAP_DISTANCE, PORT_RADIUS_IDLE, PORT_RADIUS_HOVER,
    CONN_WIDTH_MAIN, CONN_WIDTH_GLOW, CONN_WIDTH_HOVER, COLORS
)
BLOCK_REGISTRY = BLOCK_BY_NAME

# Mapeamento: bloco de escopo → (bloco de fim, bloco intermediário opcional)
# Quando o usuário arrasta um escopo, o(s) par(es) são criados automaticamente
_SCOPE_PAIRS: dict[str, list[str]] = {
    "LoopBlock":     ["EndLoopBlock"],
    "ForEachBlock":  ["EndForEachBlock"],
    "IfBlock":       ["ElseBlock", "EndIfBlock"],
    "WhileBlock":    ["EndWhileBlock"],
    "DoUntilBlock":  ["EndDoUntilBlock"],
    "TryBlock":      ["CatchBlock", "EndTryBlock"],
}

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
        
        # Novas propriedades para feedback visual premium
        self.is_hover_target = False
        self.is_valid_target = True

    @property
    def is_output(self):
        return self.port_type in ("success", "error")

    def boundingRect(self) -> QRectF:
        r = PORT_RADIUS_HOVER + 4 # Folga para o glow
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        is_active = self._hov or self.conns
        
        # Cor base
        base_color = QColor(COLORS.get(self.port_type, COLORS["default"]))
        
        if self.is_hover_target:
            # Pinta o feedback magnético
            radius = PORT_RADIUS_HOVER
            color = base_color if self.is_valid_target else QColor(COLORS["invalid"])
            glow_color = QColor(color)
            glow_color.setAlpha(80)
            
            # Glow externo
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_color)
            painter.drawEllipse(QRectF(-radius-3, -radius-3, (radius+3)*2, (radius+3)*2))
            
            # Porta principal maior
            painter.setPen(QPen(color, 2))
            painter.setBrush(color.darker(120))
            painter.drawEllipse(QRectF(-radius, -radius, radius*2, radius*2))
            
        else:
            radius = PORT_RADIUS_IDLE
            if is_active:
                painter.setPen(QPen(base_color, 1.5))
                painter.setBrush(base_color)
            else:
                painter.setPen(QPen(base_color.darker(130), 1.5))
                painter.setBrush(QColor("#1e1e2e"))
            painter.drawEllipse(QRectF(-radius, -radius, radius*2, radius*2))

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
        self.fade_mode = False

        if src:
            src.conns.append(self)
        if dst:
            dst.conns.append(self)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)
        self._redraw()
        self._hov = False
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, e):
        # Se clicar no fio com o botão esquerdo e houver dados no nó de origem
        if e.button() == Qt.LeftButton and self.src:
            data = getattr(self.src.node, "_last_data", None)
            if data:
                parent = self.scene().views()[0].window() if self.scene().views() else None
                dlg = DataViewerDialog(data, self.src.node.block_instance.name, parent)
                dlg.exec()
                e.accept()
                return
        super().mousePressEvent(e)

    def hoverEnterEvent(self, e):
        self._hov = True
        self.update()
        super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self._hov = False
        self.update()
        super().hoverLeaveEvent(e)

    def _color(self) -> str:
        if self.src:
            return COLORS.get(self.src.port_type, COLORS["default"])
        return COLORS["default"]

    def _glow_color(self) -> str:
        if self.src:
            return COLORS.get(f"glow_{self.src.port_type}", COLORS["glow_default"])
        return COLORS["glow_default"]

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

        # Bezier Curve suave
        dx   = max(abs(p1.x() - p0.x()) * 0.55, 60.0)
        path = QPainterPath(p0)
        path.cubicTo(
            QPointF(p0.x() + dx, p0.y()),
            QPointF(p1.x() - dx, p1.y()),
            p1,
        )
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        base_hex = self._color()
        base_col = QColor(base_hex)
        glow_hex = self._glow_color()
        glow_col = QColor(glow_hex)
        
        # Ajuste de opacidade para Fade Mode (quando arrastando outra conexão)
        if self.fade_mode:
            base_col.setAlpha(70) # 30% opacidade aprox
            glow_col.setAlpha(20)
        
        # Glow Effect (Linha larga com opacidade)
        glow_width = CONN_WIDTH_GLOW if self._hov else CONN_WIDTH_GLOW * 0.7
        if not self.fade_mode:
            pen_glow = QPen(glow_col, glow_width)
            pen_glow.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_glow)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self.path())
        
        # Linha Principal (Fina)
        col   = QColor("#f38ba8") if self.isSelected() else base_col
        width = CONN_WIDTH_HOVER if self.isSelected() or self._hov else CONN_WIDTH_MAIN
        
        pen_main = QPen(col, width)
        pen_main.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_main)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

        # Feedback visual de que há dados disponíveis para inspeção
        if self.src and getattr(self.src.node, "_last_data", None):
            # Desenha um pequeno brilho extra ou ícone no centro do cabo
            path = self.path()
            center_point = path.pointAtPercent(0.5)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(base_hex))
            painter.drawEllipse(center_point, 4, 4)
            
            # Halo de brilho pulsante (estático aqui, mas indica interatividade)
            glow = QColor(glow_hex)
            glow.setAlpha(150)
            painter.setBrush(glow)
            painter.drawEllipse(center_point, 7, 7)
            
            if self._hov:
                self.setToolTip("Clique para ver dados de saída")

        if self.dst:
            p1   = self.dst.scene_center()
            p0   = self.src.scene_center()
            dx   = max(abs(p1.x() - p0.x()) * 0.55, 60.0)
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
            painter.setBrush(col)
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
        self._last_result   = ""
        self._last_ok       = True
        self._last_duration = 0.0
        self._last_data     = None
        self._pinned        = False

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

    def set_result(self, message: str, ok: bool, duration: float = 0.0, data: object = None):
        self._last_result = message
        self._last_ok     = ok
        self._last_duration = duration
        self._last_data = data
        self.update()
        # Notifica conexões de saída para se atualizarem (mostra o ponto de dados)
        for c in self.success_port.conns: c.update()
        for c in self.error_port.conns: c.update()

    def shake(self):
        """Chacoalha o nó horizontalmente para sinalizar erro."""
        origin = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(350)
        anim.setEasingCurve(QEasingCurve.Linear)
        dx = 6
        anim.setKeyValueAt(0.0,  QPointF(origin.x(),      origin.y()))
        anim.setKeyValueAt(0.15, QPointF(origin.x() - dx, origin.y()))
        anim.setKeyValueAt(0.30, QPointF(origin.x() + dx, origin.y()))
        anim.setKeyValueAt(0.45, QPointF(origin.x() - dx, origin.y()))
        anim.setKeyValueAt(0.60, QPointF(origin.x() + dx, origin.y()))
        anim.setKeyValueAt(0.75, QPointF(origin.x() - dx, origin.y()))
        anim.setKeyValueAt(1.0,  QPointF(origin.x(),      origin.y()))
        self._shake_anim = anim  # mantém referência para não ser coletado
        anim.start()

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
        if self.state in ("success", "error"):
            bw = 2.5
        elif self.isSelected() or self._hov:
            bw = 2
        else:
            bw = 1
        painter.setPen(QPen(color, bw))
        painter.drawRoundedRect(rect, 10, 10)

        # Barra de cor no topo — mais grossa nos estados de resultado
        bar_h = 8 if self.state in ("success", "error") else 5
        clip = QPainterPath()
        clip.addRoundedRect(rect, 10, 10)
        painter.setClipPath(clip)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(QRectF(0, 0, NODE_W, bar_h))
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

        # ── Status Badge ──────────────────────────────────────────────────────
        if self.state in ("success", "error", "running"):
            badge_color = "#a6e3a1" if self.state == "success" else "#f38ba8"
            if self.state == "running": badge_color = "#89b4fa"

            # Círculo de fundo do badge
            badge_r = 10
            bar_h_used = 8 if self.state in ("success", "error") else 5
            center = QPointF(NODE_W - 14, bar_h_used + badge_r + 2)
            badge_rect = QRectF(center.x() - badge_r, center.y() - badge_r, badge_r*2, badge_r*2)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 80))
            painter.drawEllipse(badge_rect.translated(1, 1))
            
            painter.setPen(QPen(QColor("#11111b"), 1.5))
            painter.setBrush(QColor(badge_color))
            painter.drawEllipse(badge_rect)
            
            # Ícone
            painter.setPen(QColor("#11111b"))
            font_emoji = QFont("Segoe UI Emoji", 8, QFont.Bold)
            painter.setFont(font_emoji)
            icon = "✓" if self.state == "success" else "✗"
            if self.state == "running": icon = "⏳"
            painter.drawText(badge_rect.adjusted(0, 1, 0, 1), Qt.AlignCenter, icon)
            
            # Label de Duração
            if self.state != "running" and self._last_duration > 0:
                painter.setPen(QColor(badge_color))
                painter.setFont(QFont("Consolas", 8, QFont.Bold))
                dur_text = f"{self._last_duration:.1f}s"
                painter.drawText(QRectF(NODE_W - 60, -18, 60, 15), Qt.AlignRight | Qt.AlignVCenter, dur_text)

        # Labels das portas de saída (✓ e ✗) ou (V e F para condições)
        sy = int(NODE_H * 0.32)
        ey = int(NODE_H * 0.72)
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        
        btype = type(self.block_instance).__name__
        is_cond = btype in ("IfBlock", "WhileBlock")
        
        label_ok  = "V" if is_cond else "✓"
        label_err = "F" if is_cond else "✗"

        painter.setPen(QColor("#a6e3a1"))
        painter.drawText(QRectF(NODE_W - 18, sy - 7, 14, 14), Qt.AlignCenter, label_ok)
        painter.setPen(QColor("#f38ba8"))
        painter.drawText(QRectF(NODE_W - 18, ey - 7, 14, 14), Qt.AlignCenter, label_err)

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
        self._hov = True
        self.setToolTip(self._build_tooltip())
        self.update()
        super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self._hov = False; self.update(); super().hoverLeaveEvent(e)

    def _build_tooltip(self) -> str:
        bi   = self.block_instance
        cat  = getattr(bi, "category", "")
        desc = getattr(bi, "description", "")
        cat_icons = {
            "Navegador": "🌐", "Controle": "🔧", "Arquivos": "📁",
            "Integração": "🔌", "Sistema": "💻", "Gatilhos": "⚡",
        }
        cat_colors = {
            "Navegador": "#89b4fa", "Controle": "#cba6f7", "Arquivos": "#a6e3a1",
            "Integração": "#fab387", "Sistema": "#f38ba8", "Gatilhos": "#f9e2af",
        }
        icon       = cat_icons.get(cat, "•")
        cat_color  = cat_colors.get(cat, "#cdd6f4")

        # parâmetros configurados (exclui vazios e internos)
        param_rows = ""
        schema = getattr(bi, "params_schema", [])
        for p in schema:
            key   = p.get("name", "")
            label = p.get("label", key)
            val   = self.params.get(key)
            if val in (None, "", False):
                continue
            val_str = str(val)
            if len(val_str) > 48:
                val_str = val_str[:45] + "…"
            val_str = val_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            param_rows += (
                f"<tr>"
                f"<td style='color:#6c7086;padding:1px 8px 1px 0;white-space:nowrap'>{label}</td>"
                f"<td style='color:#cdd6f4'>{val_str}</td>"
                f"</tr>"
            )
        params_section = ""
        if param_rows:
            params_section = (
                f"<hr style='border:none;border-top:1px solid #313244;margin:6px 0'/>"
                f"<table cellspacing='0' cellpadding='0'>{param_rows}</table>"
            )

        # último resultado
        result_section = ""
        if self.state in ("success", "error") and self._last_result:
            ok_color = "#a6e3a1" if self._last_ok else "#f38ba8"
            ok_icon  = "✓" if self._last_ok else "✗"
            msg = self._last_result.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            if len(msg) > 80:
                msg = msg[:77] + "…"
            dur = f"  <span style='color:#6c7086'>({self._last_duration:.1f}s)</span>" if self._last_duration else ""
            result_section = (
                f"<hr style='border:none;border-top:1px solid #313244;margin:6px 0'/>"
                f"<div style='color:{ok_color}'>{ok_icon} {msg}{dur}</div>"
            )

        desc_section = ""
        if desc:
            d = desc[:80] + ("…" if len(desc) > 80 else "")
            d = d.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            desc_section = f"<div style='color:#6c7086;font-size:11px;margin-top:2px'>{d}</div>"

        return (
            f"<div style='"
            f"background:#1e1e2e;color:#cdd6f4;font-family:Segoe UI,sans-serif;"
            f"font-size:12px;padding:10px 12px;border-radius:8px;"
            f"border:1px solid #313244;min-width:220px'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:2px'>"
            f"  <span style='font-size:14px'>{icon}</span>"
            f"  <b style='font-size:13px;color:#cdd6f4'>{bi.name}</b>"
            f"  &nbsp;<span style='color:{cat_color};font-size:10px;font-weight:600'>{cat.upper()}</span>"
            f"</div>"
            f"{desc_section}"
            f"{params_section}"
            f"{result_section}"
            f"</div>"
        )

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
        if not sc: return
        
        # Se este nó não estiver selecionado, seleciona apenas ele
        if not self.isSelected():
            sc.clearSelection()
            self.setSelected(True)
            
        selected_nodes = [i for i in sc.selectedItems() if isinstance(i, NodeItem)]
        multi = len(selected_nodes) > 1
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background:#1e1e2e; border:1px solid #313244;
                    border-radius:6px; padding:4px; color:#cdd6f4; font-size:13px; }
            QMenu::item { padding:6px 20px; border-radius:4px; }
            QMenu::item:selected { background:#313244; color:#cba6f7; }
            QMenu::separator { background:#313244; height:1px; margin:4px 0; }
        """)
        
        if not multi:
            a_edit = menu.addAction("✏  Editar parâmetros")
            a_run  = menu.addAction("▶  Executar a partir daqui")
            menu.addSeparator()
            pin_label = "📌  Desfixar output" if self._pinned else "📌  Fixar output"
            a_pin  = menu.addAction(pin_label)
            menu.addSeparator()
        
        a_dup = menu.addAction("📋  Duplicar selecionados" if multi else "📋  Duplicar nó")
        
        a_collapse = None
        if multi:
            menu.addSeparator()
            a_collapse = menu.addAction("📦 Recolher para Sub-Processo")
            
        menu.addSeparator()
        a_del = menu.addAction("✕  Remover selecionados" if multi else "✕  Remover nó")
        
        action = menu.exec(e.screenPos())
        if action == (a_edit if not multi else None):
            sc.sig_edit_node.emit(self)
        elif action == (a_run if not multi else None):
            sc.sig_run_from_node.emit(self)
        elif action == (a_pin if not multi else None):
            self.toggle_pin()
        elif action == a_dup:
            if multi: sc.duplicate_selected()
            else: sc.duplicate_node(self)
        elif action == a_collapse:
            if hasattr(sc, "_canvas"): sc._canvas.collapse_selected_to_subflow()
        elif action == a_del:
            if multi:
                if hasattr(sc, "_canvas"): sc._canvas._push_history()
                for n in selected_nodes: sc.remove_node(n, push_history=False)
            else:
                sc.remove_node(self)


# ─────────────────────────────────────────────────────────────────────────────
# Scene
# ─────────────────────────────────────────────────────────────────────────────

class NodeScene(QGraphicsScene):
    sig_node_selected  = Signal(object)
    sig_nodes_changed  = Signal()
    sig_edit_node      = Signal(object)
    sig_run_from_node  = Signal(object)
    sig_quick_add      = Signal(object, QPointF) # (src_port, scene_pos)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nodes: list[NodeItem]        = []
        self._conns: list[ConnectionItem]  = []
        self._temp:  ConnectionItem | None = None
        self._src:   PortItem | None       = None
        self._hover_port: PortItem | None  = None
        self.selectionChanged.connect(self._on_sel_changed)

    # ── nó ────────────────────────────────────────────────────────────────────

    def add_node(self, node: NodeItem, pos: QPointF = QPointF(80, 200)) -> NodeItem:
        node.setPos(pos)
        self._nodes.append(node)
        self.addItem(node)
        self._reindex()
        return node

    def remove_item(self, item):
        """Remove qualquer item (nó, conexão, comentário, grupo) com suporte a Undo."""
        if hasattr(self, "_canvas"):
            self._canvas._push_history()
            
        if isinstance(item, NodeItem):
            self.remove_node(item, push_history=False)
        elif isinstance(item, ConnectionItem):
            self._del_conn(item, push_history=False)
            self.sig_nodes_changed.emit()
        elif isinstance(item, CommentItem):
            self.removeItem(item)
            self.sig_nodes_changed.emit()

    def remove_node(self, node: NodeItem, push_history=True):
        if push_history and hasattr(self, "_canvas"):
            self._canvas._push_history()
        all_ports = [node.in_port, node.success_port, node.error_port]
        for port in all_ports:
            for c in list(port.conns):
                self._del_conn(c, push_history=False)
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

    def duplicate_selected(self):
        """Duplica todos os nós selecionados mantendo as conexões internas."""
        selected = [i for i in self.selectedItems() if isinstance(i, NodeItem)]
        if not selected: return
        
        if hasattr(self, "_canvas"):
            self._canvas._push_history()
            
        # 1. Serializa os selecionados para facilitar a replicação com conexões
        all_steps = self.get_serialized_steps()
        sel_ids = {n.node_id for n in selected}
        subset = [copy.deepcopy(s) for s in all_steps if s.get("_id") in sel_ids]
        
        # 2. Mapeia IDs antigos para novos
        id_map = {}
        for s in subset:
            old_id = s["_id"]
            new_id = uuid.uuid4().hex[:8]
            id_map[old_id] = new_id
            s["_id"] = new_id
            s["_x"] += 60 # Offset visual
            s["_y"] += 60
            
        # 3. Ajusta conexões internas do subset
        for s in subset:
            s_next = s.get("_next_success")
            if s_next and s_next in id_map:
                s["_next_success"] = id_map[s_next]
            else:
                s.pop("_next_success", None)
                
            e_next = s.get("_next_error")
            if e_next and e_next in id_map:
                s["_next_error"] = id_map[e_next]
            else:
                s.pop("_next_error", None)

        # 4. Instancia e adiciona os novos nós
        self.clearSelection()
        node_map: dict[str, NodeItem] = {}
        
        for step in subset:
            cls = BLOCK_REGISTRY.get(step.get("block"))
            if not cls: continue
            params = step.get("params", {})
            node = NodeItem(cls(), params, step["_id"])
            self.add_node(node, QPointF(step["_x"], step["_y"]))
            node_map[step["_id"]] = node
            node.setSelected(True)
            
        # 5. Restaura conexões internas
        for step in subset:
            src_node = node_map.get(step["_id"])
            if not src_node: continue
            
            nxt_s = step.get("_next_success")
            if nxt_s and nxt_s in node_map:
                conn = ConnectionItem(src_node.success_port, node_map[nxt_s].in_port)
                self._conns.append(conn)
                self.addItem(conn)
                
            nxt_e = step.get("_next_error")
            if nxt_e and nxt_e in node_map:
                conn = ConnectionItem(src_node.error_port, node_map[nxt_e].in_port)
                self._conns.append(conn)
                self.addItem(conn)
                
        self._reindex()
        self.sig_nodes_changed.emit()

    # ── conexão ───────────────────────────────────────────────────────────────

    def _del_conn(self, conn: ConnectionItem, push_history=True):
        if push_history and hasattr(self, "_canvas"):
            self._canvas._push_history()
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

    # ── Alinhamento e Agrupamento ─────────────────────────────────────────────

    def align_selected_nodes(self, mode: str):
        """Alinha os nós selecionados conforme o modo: top, bottom, left, right, center_h, center_v."""
        selected = [i for i in self.selectedItems() if isinstance(i, NodeItem)]
        if len(selected) < 2: return
        
        xs = [n.pos().x() for n in selected]
        ys = [n.pos().y() for n in selected]
        
        if mode == "top":
            target_y = min(ys)
            for n in selected: n.setY(target_y)
        elif mode == "bottom":
            target_y = max(ys)
            for n in selected: n.setY(target_y)
        elif mode == "left":
            target_x = min(xs)
            for n in selected: n.setX(target_x)
        elif mode == "right":
            target_x = max(xs)
            for n in selected: n.setX(target_x)
        elif mode == "center_h":
            avg_y = sum(ys) / len(ys)
            for n in selected: n.setY(avg_y)
        elif mode == "center_v":
            avg_x = sum(xs) / len(xs)
            for n in selected: n.setX(avg_x)
        
        # Atualiza conexões
        for n in selected:
            n.itemChange(QGraphicsItem.ItemPositionHasChanged, n.pos())
        self.sig_nodes_changed.emit()

        # Finalização de conexão (atualmente no mouseRelease)
        pass

    # ── eventos de mouse ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, PortItem) and item.is_output:
                self._src  = item
                self._temp = ConnectionItem(item)
                self.addItem(self._temp)
                self._temp.set_tip(event.scenePos())
                
                # FADE MODE: Apaga visualmente as outras conexões
                for c in self._conns:
                    c.fade_mode = True
                    c.update()
                    
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._temp:
            pos = event.scenePos()
            
            # Reset do hover anterior
            if self._hover_port:
                self._hover_port.is_hover_target = False
                self._hover_port.update()
                self._hover_port = None

            # MAGNETIC SNAP: Busca porta de input mais próxima
            closest_port = None
            min_dist = SNAP_DISTANCE
            
            for node in self._nodes:
                p = node.in_port
                if p.node is self._src.node:
                    continue
                
                c = p.scene_center()
                dist = math.hypot(c.x() - pos.x(), c.y() - pos.y())
                if dist < min_dist:
                    min_dist = dist
                    closest_port = p
            
            if closest_port:
                closest_port.is_hover_target = True
                closest_port.is_valid_target = True
                closest_port.update()
                self._hover_port = closest_port
                
                # Snap magnético (puxa a linha)
                self._temp.set_tip(closest_port.scene_center())
            else:
                self._temp.set_tip(pos)
                
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._temp:
            # Desliga Fade Mode
            for c in self._conns:
                c.fade_mode = False
                c.update()
                
            target_port = self._hover_port
            
            # Caso não haja snap magnético, verifica hit test exato (fallback)
            if not target_port:
                item = self.itemAt(event.scenePos(), QTransform())
                if isinstance(item, PortItem) and not item.is_output and item.node is not self._src.node:
                    target_port = item
                    
            if target_port:
                target_port.is_hover_target = False
                target_port.update()
                self._hover_port = None
                
                self._temp.detach()
                self.removeItem(self._temp)
                self._make_conn(self._src, target_port)
                self.sig_nodes_changed.emit()
            else:
                # QUICK ADD: Emit signal if dropped in empty space
                src_port = self._src
                scene_pos = event.scenePos()
                self._temp.detach()
                self.removeItem(self._temp)
                self.sig_quick_add.emit(src_port, scene_pos)
                
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

    def auto_layout(self):
        """Organiza os nós em camadas usando um algoritmo de BFS simples."""
        if not self._nodes:
            return

        # 1. Mapeia adjacência e graus de entrada
        adj = {}
        in_degree = {n: 0 for n in self._nodes}
        for c in self._conns:
            if c.src and c.dst:
                adj.setdefault(c.src.node, []).append(c.dst.node)
                in_degree[c.dst.node] += 1

        # 2. Identifica raízes (nós sem entrada)
        roots = [n for n in self._nodes if in_degree[n] == 0]
        if not roots:
            # Caso haja ciclos e ninguém tenha grau 0, pega o primeiro
            roots = [self._nodes[0]]

        # 3. Distribui em camadas (BFS)
        node_layers = {}
        queue = []
        for r in roots:
            node_layers[r] = 0
            queue.append(r)

        while queue:
            u = queue.pop(0)
            layer = node_layers[u]
            for v in adj.get(u, []):
                if v not in node_layers or node_layers[v] < layer + 1:
                    node_layers[v] = layer + 1
                    queue.append(v)

        # 4. Agrupa por camada
        layers = {}
        for n, l in node_layers.items():
            layers.setdefault(l, []).append(n)
            
        # Garante que nós órfãos ou não alcançados também fiquem na camada 0 ou em uma nova
        for n in self._nodes:
            if n not in node_layers:
                node_layers[n] = 0
                layers.setdefault(0, []).append(n)

        # 5. Posiciona
        X_GAP = NODE_W + 100
        Y_GAP = NODE_H + 40
        
        # Centraliza verticalmente cada camada
        max_nodes_in_layer = max(len(ns) for ns in layers.values())
        total_max_h = max_nodes_in_layer * Y_GAP

        for l in sorted(layers.keys()):
            nodes = layers[l]
            # Ordena por Y original para preservar um pouco a intenção do usuário
            nodes.sort(key=lambda n: n.pos().y())
            
            x = l * X_GAP
            layer_h = len(nodes) * Y_GAP
            offset_y = (total_max_h - layer_h) / 2
            
            for i, n in enumerate(nodes):
                n.setPos(x, offset_y + i * Y_GAP)

        # Atualiza todas as conexões
        for c in self._conns:
            c.refresh()
        self.update()

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

        # Adiciona comentários ao final dos steps
        for item in self.items():
            if isinstance(item, CommentItem):
                result.append(item.get_data())

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
            if step.get("type") == "comment":
                c = CommentItem(
                    text=step.get("text", ""),
                    color_name=step.get("color", "Amarelo"),
                    width=step.get("width", 200),
                    height=step.get("height", 100),
                    cid=step.get("_id")
                )
                x = float(step.get("_x", 0))
                y = float(step.get("_y", 0))
                self.addItem(c)
                c.setPos(QPointF(x, y))
                continue

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
        scene._canvas = canvas # Essencial para o undo/redo funcionar na scene
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

    def contextMenuEvent(self, e):
        sc = self.scene()
        item = self.itemAt(e.pos())
        
        # Se clicou em um item, deixa o item cuidar do menu
        if item:
            super().contextMenuEvent(e)
            return
        
        # Clique no fundo vazio
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; } QMenu::item:selected { background-color: #313244; }")
        
        act_comment = menu.addAction("📝 Adicionar Comentário")
        
        selected_nodes = [i for i in sc.selectedItems() if isinstance(i, NodeItem)]
        act_collapse = None
        if selected_nodes:
            menu.addSeparator()
            act_collapse = menu.addAction("📦 Recolher para Sub-Processo")
        
        action = menu.exec(e.globalPos())
        if action == act_comment:
            scene_pos = self.mapToScene(e.pos())
            self._canvas.add_comment_at(scene_pos)
        elif action == act_collapse:
            self._canvas.collapse_selected_to_subflow()

    def keyPressEvent(self, e):
        sc = self.scene()

        # Del / Backspace — apaga selecionados
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected = list(sc.selectedItems())
            if selected:
                # Faz um único push history para a deleção múltipla
                if hasattr(self._canvas, "_push_history"):
                    self._canvas._push_history()
                for item in selected:
                    # Remove silenciosamente (sem push individual)
                    if isinstance(item, NodeItem):
                        sc.remove_node(item, push_history=False)
                    elif isinstance(item, ConnectionItem):
                        sc._del_conn(item, push_history=False)
                    elif isinstance(item, CommentItem):
                        sc.removeItem(item)
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

        # G — (Removido)
        pass
            
        # Atalhos de alinhamento (Shift + Setas / Teclas)
        if e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            if e.key() == Qt.Key_Up:    sc.align_selected_nodes("top"); e.accept(); return
            if e.key() == Qt.Key_Down:  sc.align_selected_nodes("bottom"); e.accept(); return
            if e.key() == Qt.Key_Left:  sc.align_selected_nodes("left"); e.accept(); return
            if e.key() == Qt.Key_Right: sc.align_selected_nodes("right"); e.accept(); return
            if e.key() == Qt.Key_C:     sc.align_selected_nodes("center_h"); e.accept(); return
            if e.key() == Qt.Key_V:     sc.align_selected_nodes("center_v"); e.accept(); return

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

            # Auto-cria blocos de fim/intermediários para blocos de escopo
            pair_names = _SCOPE_PAIRS.get(text, [])
            prev_node = node
            offset_x = NODE_W + 80
            for pair_name in pair_names:
                pair_cls = BLOCK_REGISTRY.get(pair_name)
                if not pair_cls:
                    continue
                pair_node = NodeItem(pair_cls(), {})
                pair_pos  = QPointF(scene_pos.x() + offset_x, scene_pos.y())
                self.scene().add_node(pair_node, pair_pos)
                # Conecta sucesso do nó anterior ao par
                if not prev_node.success_port.conns:
                    conn = ConnectionItem(prev_node.success_port, pair_node.in_port)
                    self.scene()._conns.append(conn)
                    self.scene().addItem(conn)
                    self.scene()._reindex()
                prev_node = pair_node
                offset_x += NODE_W + 80

            self._canvas._select_node(node)
            self._canvas.block_updated.emit()
        e.acceptProposedAction()


# ─────────────────────────────────────────────────────────────────────────────
# NodeCanvas — API pública idêntica a Canvas
# ─────────────────────────────────────────────────────────────────────────────

class NodeCanvas(QWidget):
    block_selected  = Signal(object)
    canvas_clicked  = Signal()
    block_updated  = Signal()
    run_from_index = Signal(int)
    request_save   = Signal()
    request_enter_subflow = Signal(object) # (node)

    _MAX_HISTORY = 30

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
        
        # Minimap flutuante
        self.minimap = Minimap(self.view, self)

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

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "minimap"):
            margin = 20
            # Posiciona no canto inferior direito
            x = self.width() - self.minimap.width() - margin
            y = self.height() - self.minimap.height() - margin
            self.minimap.move(x, y)

    # ── API pública ───────────────────────────────────────────────────────────

    def set_block_state(self, index: int, state: str):
        ordered = self.scene._ordered_nodes()
        if 0 <= index < len(ordered):
            try:
                node = ordered[index]
                node.set_state(state)
                if state == "error":
                    node.shake()
            except RuntimeError: pass

    def set_block_result(self, index: int, message: str, ok: bool = True, duration: float = 0.0, data: object = None):
        ordered = self.scene._ordered_nodes()
        if 0 <= index < len(ordered):
            try: ordered[index].set_result(message, ok, duration, data)
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

    def load_from_serialized_steps(self, steps: list):
        self.scene.load_from_steps(steps)

    def get_graph(self) -> list:
        """Retorna grafo completo para execução condicional (runner graph-aware)."""
        return self.scene.get_graph()

    def load_from_data(self, steps: list, run_auto_layout: bool = False):
        self._push_history()
        self.scene.load_from_steps(steps)
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()
        if self.scene._nodes:
            if run_auto_layout:
                self.scene.auto_layout()
            self.fit_all()

    def clear_canvas(self):
        if self.scene._nodes: self._push_history()
        self.scene.load_from_steps([])
        self._selected = None; self.canvas_clicked.emit(); self.block_updated.emit()

    def auto_layout(self):
        """Organiza visualmente o grafo e ajusta o zoom."""
        if not self.scene._nodes: return
        self._push_history()
        self.scene.auto_layout()
        self.fit_all()
        self.block_updated.emit()

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
        # Se for um bloco de subfluxo, solicita entrada em vez de abrir detalhes
        if type(node.block_instance).__name__ == "SubfluxoBlock":
            self.request_enter_subflow.emit(node)
            return

        dialog = NodeDetailsDialog(node, self)
        if dialog.exec():
            self._push_history()
            # Os parâmetros já foram atualizados por referência no _apply_to_params da dialog
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
    def add_block_at_center(self, block_cls):
        """Adiciona um bloco no centro da visualização atual (usado pela Command Palette)."""
        from ui.param_dialog import ParamDialog
        block_inst = block_cls()
        default_params = {s["name"]: s.get("default", "") for s in block_cls.params_schema}
        
        dialog = ParamDialog(block_inst, default_params, self)
        if dialog.exec():
            self._push_history()
            # Encontra o centro da view atual no sistema de coordenadas da cena
            rect = self.view.viewport().rect()
            center_scene = self.view.mapToScene(rect.center())
            node = NodeItem(block_inst, dialog.get_params())
            self.scene.add_node(node, center_scene - QPointF(NODE_W/2, NODE_H/2))
            self._select_node(node)
            self.block_updated.emit()

    def collapse_selected_to_subflow(self):
        """Transforma os nós selecionados em um único bloco de Subfluxo."""
        selected = [i for i in self.scene.selectedItems() if isinstance(i, NodeItem)]
        if not selected: return
        
        self._push_history()
        
        # 1. Calcula o centro da seleção para posicionar o novo bloco
        rect = selected[0].sceneBoundingRect()
        for n in selected[1:]:
            rect = rect.united(n.sceneBoundingRect())
        center = rect.center()
        
        # 2. Serializa os nós selecionados (apenas o sub-conjunto)
        all_steps = self.scene.get_serialized_steps()
        sel_ids = {n.node_id for n in selected}
        internal_steps = [s for s in all_steps if s.get("_id") in sel_ids]
        
        # 3. Cria o bloco de Subfluxo
        from blocks.control.subflow_block import SubfluxoBlock
        sub_node = NodeItem(SubfluxoBlock(), {
            "flow_name": "Sub-rotina Agrupada",
            "_internal_steps": internal_steps
        })
        
        # 4. Remove os nós originais (remove_node cuida das conexões)
        for n in selected:
            self.scene.remove_node(n, push_history=False)
            
        # 5. Adiciona o novo bloco de subfluxo
        # Tenta centralizar
        from ui.node_canvas import NODE_W, NODE_H
        self.scene.add_node(sub_node, center - QPointF(NODE_W/2, NODE_H/2))
        self._select_node(sub_node)
        self.block_updated.emit()

    def add_comment_at(self, scene_pos: QPointF = None):
        self._push_history()
        comment = CommentItem()
        if not scene_pos:
            rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
            scene_pos = rect.center()
        self.scene.addItem(comment)
        comment.setPos(scene_pos)
        self.block_updated.emit()

    def add_comment_at_center(self):
        self.add_comment_at(None)

    def add_block_at_pos(self, block_cls, pos: QPointF) -> "NodeItem | None":
        """Adiciona um bloco em uma posição específica e retorna o nó criado."""
        from ui.param_dialog import ParamDialog
        block_inst = block_cls()
        default_params = {s["name"]: s.get("default", "") for s in block_cls.params_schema}
        
        dialog = ParamDialog(block_inst, default_params, self)
        if dialog.exec():
            self._push_history()
            node = NodeItem(block_inst, dialog.get_params())
            self.scene.add_node(node, pos)
            self._select_node(node)
            self.block_updated.emit()
            return node
        return None

    def add_connection(self, src_port, dst_port):
        """Cria uma conexão entre duas portas."""
        if src_port and dst_port:
            self.scene._make_conn(src_port, dst_port)
            self.block_updated.emit()
