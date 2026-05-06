"""
Exporta o fluxo atual como diagrama PNG usando QPainter (sem dependências externas).
"""
from PySide6.QtGui import (
    QPainter, QPixmap, QColor, QPen, QFont,
    QFontMetrics, QPolygon, QBrush, QPainterPath,
)
from PySide6.QtCore import Qt, QRect, QPoint, QSize


# ── Paleta de cores por categoria ──────────────────────────────────────────────
_CAT_COLORS = {
    "Navegador":  ("#1a2a40", "#89b4fa"),
    "Controle":   ("#201830", "#cba6f7"),
    "Arquivos":   ("#1a2e20", "#a6e3a1"),
    "Integração": ("#2e2018", "#fab387"),
    "Sistema":    ("#2e1818", "#f38ba8"),
}
_DEFAULT_COLORS = ("#313244", "#cba6f7")

_BG       = QColor("#11111b")
_ARROW    = QColor("#45475a")

_CARD_W   = 340
_CARD_H   = 68
_CARD_R   = 10        # corner radius
_ARROW_H  = 32
_PAD_X    = 60
_PAD_TOP  = 50
_PAD_BOT  = 50


def _wrap_text(text: str, metrics: QFontMetrics, max_w: int) -> str:
    """Trunca texto com '…' se ultrapassar max_w pixels."""
    if metrics.horizontalAdvance(text) <= max_w:
        return text
    while text and metrics.horizontalAdvance(text + "…") > max_w:
        text = text[:-1]
    return text + "…"


def export_png(steps: list, output_path: str) -> str:
    """
    Renderiza o fluxo como PNG.

    steps: lista de dicts com 'block_instance' e 'params'
    output_path: caminho do arquivo .png a gerar

    Retorna o caminho gerado.
    """
    n = len(steps)
    if n == 0:
        raise ValueError("Nenhum bloco para exportar.")

    total_h = _PAD_TOP + n * _CARD_H + (n - 1) * _ARROW_H + _PAD_BOT
    total_w = _CARD_W + 2 * _PAD_X

    pixmap = QPixmap(QSize(total_w, total_h))
    pixmap.fill(_BG)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    font_name  = QFont("Segoe UI", 10, QFont.Bold)
    font_param = QFont("Consolas", 8)
    font_idx   = QFont("Segoe UI", 9, QFont.Bold)

    fm_name  = QFontMetrics(font_name)
    fm_param = QFontMetrics(font_param)

    y = _PAD_TOP

    for i, step in enumerate(steps):
        block  = step.get("block_instance")
        params = step.get("params", {})

        name     = block.name     if block else step.get("block", "?")
        category = block.category if block else "Controle"

        bg_hex, accent_hex = _CAT_COLORS.get(category, _DEFAULT_COLORS)
        bg     = QColor(bg_hex)
        accent = QColor(accent_hex)

        x = _PAD_X

        # ── Seta de conexão (exceto no primeiro) ──────────────────────
        if i > 0:
            arrow_y = y - _ARROW_H
            cx = x + _CARD_W // 2
            painter.setPen(QPen(_ARROW, 1.5))
            painter.drawLine(cx, arrow_y, cx, arrow_y + _ARROW_H - 8)
            # ponta da seta
            painter.setBrush(QBrush(_ARROW))
            painter.setPen(Qt.NoPen)
            tip = arrow_y + _ARROW_H - 1
            painter.drawPolygon(QPolygon([
                QPoint(cx - 5, tip - 8),
                QPoint(cx + 5, tip - 8),
                QPoint(cx,     tip),
            ]))

        # ── Card ──────────────────────────────────────────────────────
        path = QPainterPath()
        path.addRoundedRect(x, y, _CARD_W, _CARD_H, _CARD_R, _CARD_R)
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(accent, 1.5))
        painter.drawPath(path)

        # Círculo de índice
        idx_r = 24
        idx_x = x + 14
        idx_y = y + (_CARD_H - idx_r) // 2
        painter.setBrush(QBrush(accent))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(idx_x, idx_y, idx_r, idx_r)
        painter.setFont(font_idx)
        painter.setPen(QPen(QColor("#1e1e2e")))
        painter.drawText(QRect(idx_x, idx_y, idx_r, idx_r), Qt.AlignCenter, str(i + 1))

        # Nome do bloco
        text_x = x + idx_r + 22
        text_w = _CARD_W - text_x + x - 10
        painter.setFont(font_name)
        painter.setPen(QPen(QColor("#cdd6f4")))
        painter.drawText(
            QRect(text_x, y + 12, text_w, fm_name.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            _wrap_text(name, fm_name, text_w),
        )

        # Parâmetros resumidos
        param_parts = [f"{k}: {v}" for k, v in params.items() if v not in (None, "", False)]
        param_str   = "  ·  ".join(param_parts) if param_parts else "Sem parâmetros"
        painter.setFont(font_param)
        painter.setPen(QPen(QColor("#585b70")))
        painter.drawText(
            QRect(text_x, y + 12 + fm_name.height() + 3, text_w, fm_param.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            _wrap_text(param_str, fm_param, text_w),
        )

        y += _CARD_H + _ARROW_H

    painter.end()

    if not pixmap.save(output_path, "PNG"):
        raise IOError(f"Falha ao salvar PNG em: {output_path}")

    return output_path
