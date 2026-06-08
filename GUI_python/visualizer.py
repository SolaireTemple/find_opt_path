from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor


class Visualizer(QWidget):
    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self.size = size
        self.path = []
        self.obstacle_frames = {}
        self.current_step = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.walls = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, path, obstacle_frames, walls):
        self.path = path if path else []
        self.obstacle_frames = {frame['t']: frame['cells'] for frame in obstacle_frames} if obstacle_frames else {}
        self.walls = walls
        self.current_step = 0
        self.update()

    def start_animation(self, delay_ms=300):
        if not self.path:
            return
        self.current_step = 0
        self.timer.start(delay_ms)

    def stop_animation(self):
        self.timer.stop()

    def next_frame(self):
        if self.current_step + 1 < len(self.path):
            self.current_step += 1
            self.update()
        else:
            self.timer.stop()

    def paintEvent(self, event):
        if self.walls is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cell_w = w / self.size
        cell_h = h / self.size
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * self.size) / 2
        offset_y = (h - cell_size * self.size) / 2

        # Стены и проходы
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

        # Препятствие
        if self.path and 0 <= self.current_step < len(self.path):
            t = self.path[self.current_step][2]
            cells = self.obstacle_frames.get(t, [])
            for (x, y) in cells:
                painter.fillRect(
                    offset_x + x * cell_size,
                    offset_y + y * cell_size,
                    cell_size,
                    cell_size,
                    QColor(255, 255, 0)
                )

        # Агент
        if self.path and 0 <= self.current_step < len(self.path):
            x, y, _ = self.path[self.current_step]
            painter.fillRect(
                offset_x + x * cell_size,
                offset_y + y * cell_size,
                cell_size,
                cell_size,
                QColor(0, 255, 0)
            )

        # Старт и финиш
        if self.path:
            sx, sy, _ = self.path[0]
            ex, ey, _ = self.path[-1]
            painter.fillRect(
                offset_x + sx * cell_size,
                offset_y + sy * cell_size,
                cell_size,
                cell_size,
                QColor(0, 200, 0)
            )
            painter.fillRect(
                offset_x + ex * cell_size,
                offset_y + ey * cell_size,
                cell_size,
                cell_size,
                QColor(0, 0, 200)
            )