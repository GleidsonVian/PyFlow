"""
Gera o ícone do PyFlow RPA (icon.png + icon.ico) na pasta assets/.
Execute uma vez: python assets/generate_icon.py
"""
import sys
import math
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (
    QImage, QPainter, QColor, QPen, QBrush,
    QPainterPath, QFont, QRadialGradient, QLinearGradient,
)
from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF


def _draw_icon(size: int = 256) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    s = size
    cx, cy = s / 2, s / 2

    # ── fundo circular com gradiente ────────────────────────────────────────────
    bg = QRadialGradient(QPointF(cx, cy * 0.85), s * 0.55)
    bg.setColorAt(0.0, QColor("#2a2a45"))
    bg.setColorAt(1.0, QColor("#11111f"))
    p.setPen(Qt.NoPen)
    p.setBrush(bg)
    p.drawEllipse(QRectF(2, 2, s - 4, s - 4))

    # borda sutil
    p.setPen(QPen(QColor("#cba6f7"), s * 0.012))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QRectF(2, 2, s - 4, s - 4))

    # ── nós ─────────────────────────────────────────────────────────────────────
    nw = s * 0.22       # largura do nó
    nh = s * 0.13       # altura do nó
    r  = s * 0.035      # border-radius

    nodes = [
        (cx - s * 0.28,  cy - s * 0.06,  "#89b4fa"),   # esquerda
        (cx - s * 0.11,  cy - s * 0.24,  "#cba6f7"),   # topo
        (cx + s * 0.07,  cy - s * 0.06,  "#a6e3a1"),   # direita
    ]

    # ── conexões bezier (atrás dos nós) ────────────────────────────────────────
    def node_right_center(nx, ny):
        return QPointF(nx + nw, ny + nh / 2)

    def node_left_center(nx, ny):
        return QPointF(nx, ny + nh / 2)

    def node_top_center(nx, ny):
        return QPointF(nx + nw / 2, ny)

    conn_pen = QPen(QColor("#cba6f7"), s * 0.018)
    conn_pen.setCapStyle(Qt.RoundCap)
    p.setPen(conn_pen)
    p.setBrush(Qt.NoBrush)

    # nó 0 → nó 1  (esq → topo)
    p0 = node_right_center(*nodes[0][:2])
    p1 = node_left_center(*nodes[1][:2])
    dx = abs(p1.x() - p0.x()) * 0.55
    path = QPainterPath(p0)
    path.cubicTo(QPointF(p0.x() + dx, p0.y()),
                 QPointF(p1.x() - dx, p1.y()), p1)
    p.drawPath(path)

    # nó 1 → nó 2  (topo → dir)
    p0 = node_right_center(*nodes[1][:2])
    p1 = node_left_center(*nodes[2][:2])
    dx = abs(p1.x() - p0.x()) * 0.55
    path = QPainterPath(p0)
    path.cubicTo(QPointF(p0.x() + dx, p0.y()),
                 QPointF(p1.x() - dx, p1.y()), p1)
    p.drawPath(path)

    # nó 2 → seta de saída (indica fluxo)
    p0 = node_right_center(*nodes[2][:2])
    p1 = QPointF(p0.x() + s * 0.18, p0.y() + s * 0.14)
    path = QPainterPath(p0)
    path.cubicTo(QPointF(p0.x() + s * 0.10, p0.y()),
                 QPointF(p1.x() - s * 0.05, p1.y()), p1)
    p.drawPath(path)
    # ponta da seta
    tang = QPointF(p1.x() - s * 0.05, p1.y())
    ang  = math.atan2(p1.y() - tang.y(), p1.x() - tang.x())
    sz   = s * 0.045
    a1   = ang + math.pi * 0.75
    a2   = ang - math.pi * 0.75
    arr  = QPainterPath(p1)
    arr.lineTo(p1.x() + sz * math.cos(a1), p1.y() + sz * math.sin(a1))
    arr.lineTo(p1.x() + sz * math.cos(a2), p1.y() + sz * math.sin(a2))
    arr.closeSubpath()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#cba6f7"))
    p.drawPath(arr)

    # ── desenha cada nó ──────────────────────────────────────────────────────────
    for nx, ny, color in nodes:
        col = QColor(color)

        # sombra
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(QRectF(nx + s*0.008, ny + s*0.012, nw, nh), r, r)

        # fundo do nó
        p.setBrush(QColor("#1e1e35"))
        p.setPen(QPen(col, s * 0.010))
        p.drawRoundedRect(QRectF(nx, ny, nw, nh), r, r)

        # barra de cor no topo
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(nx, ny, nw, nh), r, r)
        p.setClipPath(clip)
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawRect(QRectF(nx, ny, nw, nh * 0.22))
        p.setClipping(False)

        # porta esquerda
        p.setPen(QPen(QColor("#8b8fa8"), s * 0.008))
        p.setBrush(QColor("#1e1e35"))
        p.drawEllipse(QPointF(nx, ny + nh / 2), s * 0.018, s * 0.018)

        # porta direita (saída)
        p.setPen(QPen(col, s * 0.008))
        p.setBrush(col)
        p.drawEllipse(QPointF(nx + nw, ny + nh / 2), s * 0.018, s * 0.018)

    # ── texto "PF" centralizado abaixo dos nós ───────────────────────────────
    font = QFont("Segoe UI", int(s * 0.155), QFont.Bold)
    p.setFont(font)

    text_y = cy + s * 0.14
    text_rect = QRectF(0, text_y, s, s * 0.22)

    # sombra do texto
    p.setPen(QColor(0, 0, 0, 120))
    p.drawText(text_rect.translated(s * 0.006, s * 0.006), Qt.AlignCenter, "PyFlow")

    # gradiente no texto
    grad = QLinearGradient(QPointF(cx - s*0.2, 0), QPointF(cx + s*0.2, 0))
    grad.setColorAt(0.0, QColor("#89b4fa"))
    grad.setColorAt(0.5, QColor("#cba6f7"))
    grad.setColorAt(1.0, QColor("#a6e3a1"))
    p.setPen(QPen(QBrush(grad), 1))
    p.drawText(text_rect, Qt.AlignCenter, "PyFlow")

    # ── linha decorativa embaixo do texto ───────────────────────────────────
    lw = s * 0.35
    lx = cx - lw / 2
    ly = text_y + s * 0.20
    lg = QLinearGradient(QPointF(lx, ly), QPointF(lx + lw, ly))
    lg.setColorAt(0.0,  QColor("#89b4fa00"))
    lg.setColorAt(0.25, QColor("#89b4fa"))
    lg.setColorAt(0.75, QColor("#cba6f7"))
    lg.setColorAt(1.0,  QColor("#cba6f700"))
    p.setPen(QPen(QBrush(lg), s * 0.008))
    p.drawLine(QPointF(lx, ly), QPointF(lx + lw, ly))

    p.end()
    return img


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Gera PNG 256
    img256 = _draw_icon(256)
    png_path = out_dir / "icon.png"
    img256.save(str(png_path), "PNG")
    print(f"[OK] {png_path}")

    # Gera ICO com múltiplos tamanhos embutidos
    ico_path = out_dir / "icon.ico"
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for sz in sizes:
        images.append(_draw_icon(sz))

    # PySide6 salva ICO diretamente (usa o primeiro tamanho)
    # Para ICO multi-size precisamos do Pillow — tenta, se não houver salva PNG
    try:
        from PIL import Image
        pil_imgs = []
        for qi in images:
            qi_rgba = qi.convertToFormat(QImage.Format.Format_RGBA8888)
            raw = bytes(qi_rgba.bits())
            pi = Image.frombytes("RGBA", (qi_rgba.width(), qi_rgba.height()), raw)
            pil_imgs.append(pi)
        pil_imgs[0].save(
            str(ico_path), format="ICO",
            sizes=[(im.width, im.height) for im in pil_imgs],
            append_images=pil_imgs[1:],
        )
        print(f"[OK] {ico_path}  (multi-size ICO com Pillow)")
    except ImportError:
        # Sem Pillow: salva ICO de tamanho único via QImage
        img32 = _draw_icon(32)
        img32.save(str(ico_path), "ICO")
        print(f"[OK] {ico_path}  (ICO simples — instale Pillow para multi-size)")
    except Exception as ex:
        # Fallback: copia o PNG como ICO (funciona no Windows)
        import shutil
        shutil.copy(str(png_path), str(ico_path))
        print(f"[OK] {ico_path}  (ICO via cópia PNG — fallback: {ex})")

    print("\nÍcone gerado com sucesso!")


if __name__ == "__main__":
    main()
