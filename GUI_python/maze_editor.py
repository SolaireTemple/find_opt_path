from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QMouseEvent


class MazeEditor(QWidget):
    data_changed = Signal()

    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self.size = size
        self.walls = [[False] * size for _ in range(size)]
        self.start = (0, 0)
        self.exit = (size - 1, size - 1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_cell_type(self, x, y, button):
        if button == Qt.LeftButton:
            self.walls[y][x] = not self.walls[y][x]
        elif button == Qt.RightButton:
            if (x, y) == self.start:
                self.start = None
            elif (x, y) == self.exit:
                self.exit = None
            else:
                if self.start is None:
                    self.start = (x, y)
                elif self.exit is None:
                    self.exit = (x, y)
                else:
                    self.start = (x, y)
        self.update()
        self.data_changed.emit()

    def mousePressEvent(self, event: QMouseEvent):
        w = self.width()
        h = self.height()
        cell_w = w / self.size
        cell_h = h / self.size
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * self.size) / 2
        offset_y = (h - cell_size * self.size) / 2
        x = int((event.x() - offset_x) // cell_size)
        y = int((event.y() - offset_y) // cell_size)
        if 0 <= x < self.size and 0 <= y < self.size:
            self.set_cell_type(x, y, event.button())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        cell_w = w / self.size
        cell_h = h / self.size
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * self.size) / 2
        offset_y = (h - cell_size * self.size) / 2

        for y in range(self.size):
            for x in range(self.size):
                rect = QRectF(
                    offset_x + x * cell_size,
                    offset_y + y * cell_size,
                    cell_size,
                    cell_size
                )
                if self.walls[y][x]:
                    painter.fillRect(rect, QColor(80, 80, 80))
                else:
                    painter.fillRect(rect, QColor(255, 255, 255))
                painter.drawRect(rect)

        if self.start:
            sx, sy = self.start
            painter.fillRect(
                offset_x + sx * cell_size,
                offset_y + sy * cell_size,
                cell_size,
                cell_size,
                QColor(0, 255, 0)
            )
        if self.exit:
            ex, ey = self.exit
            painter.fillRect(
                offset_x + ex * cell_size,
                offset_y + ey * cell_size,
                cell_size,
                cell_size,
                QColor(0, 0, 255)
            )

    def get_walls_matrix(self):
        return [[1 if self.walls[y][x] else 0 for x in range(self.size)] for y in range(self.size)]

    def get_start(self):
        return self.start if self.start else (0, 0)

    def get_exit(self):
        return self.exit if self.exit else (self.size - 1, self.size - 1)