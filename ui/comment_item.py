from PySide6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QMenu
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QTextCursor, QPainterPath

COMMENT_COLORS = {
    "Amarelo": {"bg": "#f9e2af", "text": "#11111b"},
    "Azul":    {"bg": "#89b4fa", "text": "#11111b"},
    "Verde":   {"bg": "#a6e3a1", "text": "#11111b"},
    "Rosa":    {"bg": "#f5c2e7", "text": "#11111b"},
    "Cinza":   {"bg": "#45475a", "text": "#cdd6f4"}
}

class EditableTextItem(QGraphicsTextItem):
    def focusInEvent(self, event):
        if self.parentItem():
            self.parentItem().setFlag(QGraphicsObject.ItemIsMovable, False)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        if self.parentItem():
            self.parentItem().setFlag(QGraphicsObject.ItemIsMovable, True)
        super().focusOutEvent(event)

class CommentItem(QGraphicsObject):
    sig_changed = Signal()

    def __init__(self, text="Duplo clique para editar", color_name="Amarelo", width=200, height=100, cid=None):
        super().__init__()
        import uuid
        self.comment_id = cid or uuid.uuid4().hex[:8]
        self.color_name = color_name
        self._width = width
        self._height = height

        self.setFlags(
            QGraphicsObject.ItemIsSelectable |
            QGraphicsObject.ItemIsMovable |
            QGraphicsObject.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(-100) # Fica muito atrás de tudo

        self._resizing = False

        # Texto editável embutido
        self.text_item = EditableTextItem(self)
        self.text_item.setPlainText(text)
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        font = QFont("Segoe UI", 11)
        self.text_item.setFont(font)
        self._update_text_color()
        self.text_item.setPos(10, 10)
        self.text_item.setTextWidth(self._width - 20)
        
        # Conecta sinal para ajustar altura automaticamente se texto crescer
        self.text_item.document().contentsChanged.connect(self._on_text_changed)

    def boundingRect(self):
        return QRectF(0, 0, self._width, self._height)

    def _update_text_color(self):
        color = QColor(COMMENT_COLORS.get(self.color_name, COMMENT_COLORS["Amarelo"])["text"])
        self.text_item.setDefaultTextColor(color)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        theme = COMMENT_COLORS.get(self.color_name, COMMENT_COLORS["Amarelo"])
        
        bg_color = QColor(theme["bg"])
        bg_color.setAlpha(200) # Leve transparência
        
        if self.isSelected():
            painter.setPen(QPen(QColor("#cdd6f4"), 2, Qt.DashLine))
        else:
            painter.setPen(Qt.NoPen)
            
        painter.setBrush(bg_color)
        painter.drawRoundedRect(self.boundingRect(), 8, 8)

        # Handle de redimensionamento
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 40))
        handle_path = QPainterPath()
        handle_path.moveTo(self._width - 15, self._height)
        handle_path.lineTo(self._width, self._height - 15)
        handle_path.lineTo(self._width, self._height)
        handle_path.closeSubpath()
        painter.drawPath(handle_path)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        if pos.x() > self._width - 15 and pos.y() > self._height - 15:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.text_item.setFocus()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        pos = event.pos()
        if pos.x() > self._width - 15 and pos.y() > self._height - 15:
            if event.button() == Qt.LeftButton:
                self._resizing = True
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            pos = event.pos()
            new_w = max(100, pos.x())
            new_h = max(50, pos.y())
            if new_w != self._width or new_h != self._height:
                self.prepareGeometryChange()
                self._width = new_w
                self._height = new_h
                self.text_item.setTextWidth(self._width - 20)
                self.update()
                self.sig_changed.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; } QMenu::item:selected { background-color: #313244; }")
        
        # Ações de Cor
        for c_name in COMMENT_COLORS.keys():
            act = menu.addAction(f"Cor: {c_name}")
            act.triggered.connect(lambda checked=False, c=c_name: self.set_color(c))
            
        menu.addSeparator()
        delete_act = menu.addAction("Excluir")
        delete_act.triggered.connect(self._delete_self)
        
        menu.exec(event.screenPos())

    def set_color(self, color_name):
        self.color_name = color_name
        self._update_text_color()
        self.update()
        self.sig_changed.emit()

    def _delete_self(self):
        if self.scene():
            self.scene().removeItem(self)
            self.sig_changed.emit()

    def _on_text_changed(self):
        doc_h = self.text_item.document().size().height()
        if doc_h + 20 > self._height:
            self.prepareGeometryChange()
            self._height = doc_h + 20
        self.update()
        self.sig_changed.emit()

    def itemChange(self, change, value):
        if change == QGraphicsObject.ItemPositionHasChanged:
            self.sig_changed.emit()
        return super().itemChange(change, value)
        
    def get_data(self):
        return {
            "type": "comment",
            "text": self.text_item.toPlainText(),
            "color": self.color_name,
            "_x": round(self.pos().x(), 1),
            "_y": round(self.pos().y(), 1),
            "width": self._width,
            "height": self._height
        }
