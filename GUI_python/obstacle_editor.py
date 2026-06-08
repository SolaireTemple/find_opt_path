from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QSpinBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QMouseEvent, QPen


class ObstacleEditor(QWidget):
    data_changed = Signal()  # сигнал об изменении формы или маршрута

    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self.size = size
        self.walls = None
        self.start = (0, 0)
        self.exit = (self.size - 1, self.size - 1)

        # Данные препятствия
        self.shape_cells = set()   # абсолютные координаты клеток формы
        self.route_points = []     # список позиций опорной точки (абсолютные координаты)
        self.mode = "cyclic"
        self.speed = 1

        self.edit_mode = "shape"   # "shape" или "route"

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_controls()
        self._update_status_label()

        # Сигналы от виджетов
        self.mode_combo.currentTextChanged.connect(self.set_mode)
        self.set_mode(self.mode_combo.currentText())

        self.speed_spin.valueChanged.connect(self.set_speed)
        self.shape_btn.clicked.connect(lambda: self.set_edit_mode("shape"))
        self.route_btn.clicked.connect(lambda: self.set_edit_mode("route"))
        self.clear_shape_btn.clicked.connect(self.clear_shape)
        self.clear_route_btn.clicked.connect(self.clear_route)
        self.undo_route_btn.clicked.connect(self.undo_last_route_point)

        # Кнопки перемещения (для маршрута)
        self.move_up.clicked.connect(lambda: self.move_obstacle(0, -1))
        self.move_down.clicked.connect(lambda: self.move_obstacle(0, 1))
        self.move_left.clicked.connect(lambda: self.move_obstacle(-1, 0))
        self.move_right.clicked.connect(lambda: self.move_obstacle(1, 0))

    def _build_controls(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Параметры движения
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Режим:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["once", "cyclic", "back_and_forth"])
        params_layout.addWidget(self.mode_combo)
        params_layout.addWidget(QLabel("Скорость:"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setMinimum(1)
        self.speed_spin.setMaximum(10)
        self.speed_spin.setValue(1)
        params_layout.addWidget(self.speed_spin)
        params_layout.addStretch()
        main_layout.addLayout(params_layout)

        # Кнопки выбора режима редактирования
        edit_layout = QHBoxLayout()
        self.shape_btn = QPushButton("Форма")
        self.shape_btn.setCheckable(True)
        self.shape_btn.setChecked(True)
        self.route_btn = QPushButton("Маршрут")
        self.route_btn.setCheckable(True)
        edit_layout.addWidget(self.shape_btn)
        edit_layout.addWidget(self.route_btn)
        edit_layout.addStretch()
        main_layout.addLayout(edit_layout)

        # Холст с прокруткой
        self.canvas = QWidget()
        self.canvas.mousePressEvent = self.canvas_mouse_press
        self.canvas.paintEvent = self.draw_canvas
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll, 1)

        # Кнопки для перемещения препятствия (при задании маршрута)
        move_layout = QHBoxLayout()
        self.move_up = QPushButton("↑ Вверх")
        self.move_down = QPushButton("↓ Вниз")
        self.move_left = QPushButton("← Влево")
        self.move_right = QPushButton("→ Вправо")
        for btn in [self.move_up, self.move_down, self.move_left, self.move_right]:
            btn.setEnabled(False)
            move_layout.addWidget(btn)
        main_layout.addLayout(move_layout)

        # Кнопки управления маршрутом
        route_buttons_layout = QHBoxLayout()
        self.clear_shape_btn = QPushButton(" Очистить форму")
        self.clear_route_btn = QPushButton("Очистить маршрут")
        self.undo_route_btn = QPushButton("Отменить шаг")
        route_buttons_layout.addWidget(self.clear_shape_btn)
        route_buttons_layout.addWidget(self.clear_route_btn)
        route_buttons_layout.addWidget(self.undo_route_btn)
        main_layout.addLayout(route_buttons_layout)

        # Статусная строка
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #f0f0f0; padding: 4px;")
        main_layout.addWidget(self.status_label)

    def _update_status_label(self):
        if self.edit_mode == "shape":
            self.status_label.setText(
                "Режим: рисование ФОРМЫ. Кликайте по свободным клеткам, чтобы добавлять/удалять жёлтые клетки."
            )
        else:
            self.status_label.setText(
                "Режим: МАРШРУТ. Используйте стрелки для перемещения препятствия. Каждое перемещение добавляет точку маршрута."
            )

    def set_edit_mode(self, mode):
        self.edit_mode = mode
        self.shape_btn.setChecked(mode == "shape")
        self.route_btn.setChecked(mode == "route")
        enabled = (mode == "route")
        for btn in [self.move_up, self.move_down, self.move_left, self.move_right]:
            btn.setEnabled(enabled)
        self._update_status_label()
        self.canvas.update()

    def update_maze_data(self, walls, start, exit):
        """Вызывается из контроллера для синхронизации лабиринта."""
        self.walls = walls
        self.start = start if start else (0, 0)
        self.exit = exit if exit else (self.size - 1, self.size - 1)
        self.canvas.update()

    def canvas_mouse_press(self, event: QMouseEvent):
        if self.edit_mode != "shape":
            return
        # Вычисляем координаты клетки (с учётом масштабирования)
        w = self.canvas.width()
        h = self.canvas.height()
        cell_w = w / self.size
        cell_h = h / self.size
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * self.size) / 2
        offset_y = (h - cell_size * self.size) / 2
        x = int((event.x() - offset_x) // cell_size)
        y = int((event.y() - offset_y) // cell_size)
        if 0 <= x < self.size and 0 <= y < self.size:
            # Нельзя ставить форму на стену, старт или финиш
            if self.walls[y][x] or (x, y) == self.start or (x, y) == self.exit:
                return
            if (x, y) in self.shape_cells:
                self.shape_cells.remove((x, y))
            else:
                self.shape_cells.add((x, y))
            self.canvas.update()
            self.data_changed.emit()

    def draw_canvas(self, event):
        if self.walls is None:
            return
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.canvas.width()
        h = self.canvas.height()
        cell_w = w / self.size
        cell_h = h / self.size
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * self.size) / 2
        offset_y = (h - cell_size * self.size) / 2

        # Фон и стены
        for y in range(self.size):
            for x in range(self.size):
                rect = QRectF(offset_x + x*cell_size, offset_y + y*cell_size, cell_size, cell_size)
                if self.walls[y][x]:
                    painter.fillRect(rect, QColor(80,80,80))
                else:
                    painter.fillRect(rect, QColor(240,240,240))
                painter.drawRect(rect)

        # Старт и финиш
        if self.start:
            sx, sy = self.start
            painter.fillRect(offset_x + sx*cell_size, offset_y + sy*cell_size, cell_size, cell_size, QColor(0,200,0))
        if self.exit:
            ex, ey = self.exit
            painter.fillRect(offset_x + ex*cell_size, offset_y + ey*cell_size, cell_size, cell_size, QColor(0,0,200))

        # Форма препятствия (жёлтые клетки)
        for (x,y) in self.shape_cells:
            painter.fillRect(offset_x + x*cell_size, offset_y + y*cell_size, cell_size, cell_size, QColor(255,255,0, 180))

        # Маршрут (красные точки опорной позиции)
        if len(self.route_points) > 1:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            for i in range(len(self.route_points)-1):
                x1,y1 = self.route_points[i]
                x2,y2 = self.route_points[i+1]
                painter.drawLine(
                    offset_x + x1*cell_size + cell_size/2,
                    offset_y + y1*cell_size + cell_size/2,
                    offset_x + x2*cell_size + cell_size/2,
                    offset_y + y2*cell_size + cell_size/2
                )
        for (x,y) in self.route_points:
            painter.fillRect(offset_x + x*cell_size, offset_y + y*cell_size, cell_size, cell_size, QColor(255,100,100, 180))

    def move_obstacle(self, dx, dy):
        """Перемещает всю форму на (dx, dy) и добавляет новую позицию опорной точки в маршрут."""
        if not self.shape_cells:
            # Если формы нет, ничего не делаем
            return
        # Проверяем, можно ли сдвинуть
        new_cells = set()
        for (x,y) in self.shape_cells:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= self.size or ny < 0 or ny >= self.size:
                return
            if self.walls[ny][nx]:
                return
            if (nx, ny) == self.start or (nx, ny) == self.exit:
                return
            new_cells.add((nx, ny))
        # Применяем сдвиг
        self.shape_cells = new_cells
        # Вычисляем новую опорную точку (минимальные координаты)
        min_x = min(p[0] for p in self.shape_cells)
        min_y = min(p[1] for p in self.shape_cells)
        self.route_points.append((min_x, min_y))
        self.canvas.update()
        self.data_changed.emit()

    def undo_last_route_point(self):
        if len(self.route_points) > 1:
            # Откатываем последнюю точку маршрута, но форму не возвращаем (оставляем в текущем положении)
            self.route_points.pop()
            self.canvas.update()
            self.data_changed.emit()
        elif len(self.route_points) == 1:
            # Если осталась только начальная точка, удалить её? Не будем.
            pass

    def clear_shape(self):
        self.shape_cells.clear()
        self.route_points.clear()  # также очищаем маршрут
        self.canvas.update()
        self.data_changed.emit()

    def clear_route(self):
        # Очищает маршрут, но форму оставляет
        if self.shape_cells:
            min_x = min(p[0] for p in self.shape_cells)
            min_y = min(p[1] for p in self.shape_cells)
            self.route_points = [(min_x, min_y)]
        else:
            self.route_points = []
        self.canvas.update()
        self.data_changed.emit()

    def set_shape_cells(self, cells):
        """cells – список абсолютных координат (x, y) клеток формы"""
        self.shape_cells = set(cells)
        self.canvas.update()
        self.data_changed.emit()

    def set_route_points(self, points):
        """points – список абсолютных координат (x, y) опорных точек маршрута"""
        self.route_points = list(points)
        self.canvas.update()
        self.data_changed.emit()

    def set_mode(self, mode):
        self.mode = mode
        # Синхронизация комбобокса
        idx = self.mode_combo.findText(mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.data_changed.emit()

    def set_speed(self, speed):
        self.speed = speed
        self.speed_spin.setValue(speed)
        self.data_changed.emit()

    def get_shape(self):
        """Возвращает список смещений (dx,dy) относительно минимальной точки формы."""
        if not self.shape_cells:
            return [(0,0)]
        min_x = min(p[0] for p in self.shape_cells)
        min_y = min(p[1] for p in self.shape_cells)
        return [(x - min_x, y - min_y) for (x,y) in self.shape_cells]

    def get_route(self):
        """Возвращает список абсолютных координат опорной точки маршрута."""
        if not self.route_points and self.shape_cells:
            min_x = min(p[0] for p in self.shape_cells)
            min_y = min(p[1] for p in self.shape_cells)
            return [(min_x, min_y)]
        return self.route_points if self.route_points else [(0,0)]

    def get_mode(self):
        return self.mode

    def get_speed(self):
        return self.speed

    def set_mode(self, mode):
        self.mode = mode
        self.data_changed.emit()

    def set_speed(self, speed):
        self.speed = speed
        self.data_changed.emit()