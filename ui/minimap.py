from PySide6.QtWidgets import QGraphicsView, QWidget
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class Minimap(QGraphicsView):
    """
    Mini-mapa flutuante para navegação rápida no canvas de nós.
    Mostra uma visão geral do grafo e permite clicar/arrastar para mover a câmera principal.
    """
    def __init__(self, main_view, parent=None):
        super().__init__(parent)
        self.main_view = main_view
        self.setScene(main_view.scene())
        
        # Desativa interações padrão de scroll e itens
        self.setInteractive(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Renderização suave
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Estilo visual moderno e translúcido
        self.setFixedSize(220, 140)
        self.setStyleSheet("""
            QGraphicsView {
                background: rgba(24, 24, 37, 200); 
                border: 1px solid #313244; 
                border-radius: 10px;
            }
        """)
        
        # Timer para atualizar o retângulo do viewport periodicamente (ou sob demanda)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update)
        self.refresh_timer.start(50) # 20 FPS para o minimapa é suficiente

    def drawForeground(self, painter, rect):
        """Desenha o retângulo que representa o que o usuário vê na tela principal."""
        # Obtém o retângulo da cena visível na view principal
        # Precisamos converter o rect do viewport da view principal para coordenadas da cena
        v_rect = self.main_view.viewport().rect()
        scene_rect = self.main_view.mapToScene(v_rect).boundingRect()
        
        # Estilo do retângulo do viewport (roxo catppuccin)
        painter.setPen(QPen(QColor("#cba6f7"), 1.5))
        painter.setBrush(QBrush(QColor(203, 166, 247, 30)))
        painter.drawRect(scene_rect)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._scroll_to(e.position())
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self._scroll_to(e.position())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def _scroll_to(self, pos):
        """Move a câmera principal para o ponto clicado no minimapa."""
        scene_pos = self.mapToScene(pos.toPoint())
        self.main_view.centerOn(scene_pos)
        self.update()

    def paintEvent(self, e):
        # Ajusta o zoom do minimapa para sempre mostrar todos os itens com uma margem
        items_rect = self.scene().itemsBoundingRect()
        if not items_rect.isNull():
            # Dá um "padding" para o minimapa não ficar colado nas bordas
            padding = 200
            self.fitInView(items_rect.adjusted(-padding, -padding, padding, padding), Qt.KeepAspectRatio)
        super().paintEvent(e)
