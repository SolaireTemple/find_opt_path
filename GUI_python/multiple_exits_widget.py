import os
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QLabel, QScrollArea, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor

STEPS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

# ---------- Вспомогательные функции ----------
def read_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    n, m = map(int, lines[0].split())
    matrix = [[float(num) for num in line.split()] for line in lines[1:n + 1]]
    return matrix

def get_n_wave(M, n):
    for _ in range(n):
        for i in range(len(M)):
            for j in range(len(M[i])):
                if M[i][j] == _:
                    for dx, dy in STEPS:
                        x, y = i + dx, j + dy
                        if 0 <= x < len(M) and 0 <= y < len(M[i]) and M[x][y] == -1:
                            M[x][y] = _ + 1

def intersect(matrices):
    rows, cols = len(matrices[0]), len(matrices[0][0])
    result = [[-1] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            val = matrices[0][i][j]
            for m in matrices[1:]:
                if val == -2 or m[i][j] == -2:
                    val = -2
                elif val >= 0 and m[i][j] >= 0:
                    val = 0
                elif val == -1 or m[i][j] == -1:
                    val = -1
            result[i][j] = val
    return result

# ---------- Функции для построения пути ----------
def bfs_to_W0(start, W0_matrix, walls):
    rows, cols = len(walls), len(walls[0])
    queue = deque()
    queue.append((start[0], start[1], [start]))
    visited = set()
    visited.add(start)
    while queue:
        x, y, path = queue.popleft()
        if W0_matrix[y][x] == 0:
            return path
        for dx, dy in STEPS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and walls[ny][nx] != -2 and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, path + [(nx, ny)]))
    return None

def build_path_to_exit(start_cell, exit_cell, dist_matrix):
    x, y = start_cell
    path = [(x, y)]
    while (x, y) != exit_cell:
        min_val = float('inf')
        best = None
        for dx, dy in STEPS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(dist_matrix[0]) and 0 <= ny < len(dist_matrix):
                if dist_matrix[ny][nx] >= 0 and dist_matrix[ny][nx] < min_val:
                    min_val = dist_matrix[ny][nx]
                    best = (nx, ny)
        if best is None:
            return None
        x, y = best
        path.append((x, y))
    return path

def find_exit_cell(cell, exit_matrices, max_steps):
    x, y = cell
    for mat in exit_matrices:
        if mat[y][x] != -1 and mat[y][x] <= max_steps:
            for i in range(len(mat)):
                for j in range(len(mat[0])):
                    if mat[i][j] == 0:
                        return (j, i)
    return None

# ---------- Виджет для отображения матрицы ----------
class MatrixWidget(QWidget):
    def __init__(self, matrix, parent=None):
        super().__init__(parent)
        self.matrix = matrix
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_matrix(self, matrix):
        self.matrix = matrix
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rows = len(self.matrix)
        cols = len(self.matrix[0])
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return
        cell_w = w / cols
        cell_h = h / rows
        cell_size = min(cell_w, cell_h)
        offset_x = (w - cell_size * cols) / 2
        offset_y = (h - cell_size * rows) / 2
        for i in range(rows):
            for j in range(cols):
                rect = QRectF(offset_x + j * cell_size, offset_y + i * cell_size, cell_size, cell_size)
                val = self.matrix[i][j]
                if val == -2:
                    painter.fillRect(rect, QColor(80, 80, 80))
                elif val == -1:
                    painter.fillRect(rect, QColor(240, 240, 240))
                elif val == 0:
                    painter.fillRect(rect, QColor(100, 200, 100))
                elif val > 0:
                    painter.fillRect(rect, QColor(50, 150, 250))
                painter.drawRect(rect)

# ---------- Основной виджет для задачи с неизвестными выходами ----------
class MultipleExitsWidget(QWidget):
    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self.size = size
        self.matrices = []
        self.W0 = None
        self.stage_matrices = []
        self.anim_matrices = None
        self.anim_current_step = 0
        self.anim_total_steps = 0
        self.anim_widgets = []
        self.timer_stage1 = QTimer()
        self.timer_stage1.timeout.connect(self.do_wave_step)

        self.final_mat = None
        self.final_anim_mat = None
        self.final_anim_step = 0
        self.final_anim_total = 0
        self.final_widget = None
        self.timer_stage3 = QTimer()
        self.timer_stage3.timeout.connect(self.do_final_wave_step)

        # Стартовая точка (задаём по умолчанию (0,0))
        self.start_point = (2, 0)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        btn_load = QPushButton("Загрузить карты выходов (файлы file0.txt, file1.txt, ...)")
        btn_load.clicked.connect(self.load_matrices)
        layout.addWidget(btn_load)

        btn_layout = QHBoxLayout()
        self.btn_stage1 = QPushButton("Этап 1: Волны для каждого выхода")
        self.btn_stage1.setEnabled(False)
        self.btn_stage1.clicked.connect(self.start_stage1)
        self.btn_stage2 = QPushButton("Этап 2: Пересечение карт (W0)")
        self.btn_stage2.setEnabled(False)
        self.btn_stage2.clicked.connect(self.show_stage2)
        self.btn_stage3 = QPushButton("Этап 3: Финальная волна от W0")
        self.btn_stage3.setEnabled(False)
        self.btn_stage3.clicked.connect(self.start_stage3)
        btn_layout.addWidget(self.btn_stage1)
        btn_layout.addWidget(self.btn_stage2)
        btn_layout.addWidget(self.btn_stage3)

        # Кнопка этапа 4
        self.btn_stage4 = QPushButton("Этап 4: Построить путь")
        self.btn_stage4.setEnabled(False)
        self.btn_stage4.clicked.connect(self.show_full_path)
        btn_layout.addWidget(self.btn_stage4)

        layout.addLayout(btn_layout)

        self.info_label = QLabel("Загрузите карты (несколько файлов). Стартовая точка: (0,0)")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.display_widget = QWidget()
        self.display_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.display_layout = QVBoxLayout(self.display_widget)
        self.display_layout.setAlignment(Qt.AlignTop)
        self.display_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.display_widget)
        layout.addWidget(self.scroll_area, 1)

        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("p (макс. шагов):"))
        self.p_spin = QSpinBox()
        self.p_spin.setRange(1, 20)
        self.p_spin.setValue(7)
        param_layout.addWidget(self.p_spin)
        param_layout.addWidget(QLabel("τ (шаги после пересечения):"))
        self.tau_spin = QSpinBox()
        self.tau_spin.setRange(0, 10)
        self.tau_spin.setValue(2)
        param_layout.addWidget(self.tau_spin)
        layout.addLayout(param_layout)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                pass

    def propagate_one_step(self, M, m):
        rows, cols = len(M), len(M[0])
        updates = []
        for i in range(rows):
            for j in range(cols):
                if M[i][j] == m:
                    for dx, dy in STEPS:
                        x, y = i + dx, j + dy
                        if 0 <= x < rows and 0 <= y < cols and M[x][y] == -1:
                            updates.append((x, y))
        for (x, y) in updates:
            M[x][y] = m + 1

    def start_stage1(self):
        p = self.p_spin.value()
        tau = self.tau_spin.value()
        steps = p - tau
        if steps <= 0:
            QMessageBox.warning(self, "Ошибка", "p - τ должно быть > 0")
            return
        if not self.matrices:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите карты")
            return
        self.timer_stage1.stop()
        self.anim_matrices = [ [row[:] for row in m] for m in self.matrices ]
        self.anim_current_step = 0
        self.anim_total_steps = steps
        self.clear_layout(self.display_layout)

        self.display_layout.addStretch()

        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setSpacing(15)
        h_layout.addStretch(3)

        self.anim_widgets = []
        for idx, mat in enumerate(self.anim_matrices):
            col_layout = QVBoxLayout()
            col_layout.setAlignment(Qt.AlignCenter)
            label = QLabel(f"Карта выхода {idx+1} (шаг 0 из {steps})")
            label.setAlignment(Qt.AlignCenter)
            col_layout.addWidget(label)
            widget = MatrixWidget(mat)
            col_layout.addWidget(widget)
            h_layout.addLayout(col_layout, 4)
            self.anim_widgets.append(widget)

        h_layout.addStretch(3)
        h_container.setLayout(h_layout)

        self.display_layout.addWidget(h_container, 1)
        self.display_layout.addStretch()

        self.timer_stage1.start(300)
        self.btn_stage2.setEnabled(False)
        self.btn_stage3.setEnabled(False)
        self.btn_stage4.setEnabled(False)
        self.info_label.setText("Анимация распространения волны (этап 1)...")

    def do_wave_step(self):
        if self.anim_current_step >= self.anim_total_steps:
            self.timer_stage1.stop()
            self.stage_matrices = [ [row[:] for row in mat] for mat in self.anim_matrices ]
            self.info_label.setText("Этап 1 завершён. Перейдите к Этапу 2.")
            self.btn_stage2.setEnabled(True)
            self.btn_stage3.setEnabled(False)
            return
        for mat in self.anim_matrices:
            self.propagate_one_step(mat, self.anim_current_step)
        for widget in self.anim_widgets:
            widget.update()
        labels = []
        for child in self.display_widget.findChildren(QLabel):
            if "шаг" in child.text():
                labels.append(child)
        for i, label in enumerate(labels):
            if i < len(self.anim_widgets):
                label.setText(f"Карта выхода {i+1} (шаг {self.anim_current_step+1} из {self.anim_total_steps})")
        self.anim_current_step += 1

    def show_stage2(self):
        if not self.stage_matrices:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните Этап 1")
            return
        self.W0 = intersect(self.stage_matrices)
        self.clear_layout(self.display_layout)

        self.display_layout.addStretch()

        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.addStretch(3)

        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignCenter)
        label = QLabel("Пересечение карт W0 (зелёные клетки – достижимы из всех выходов)")
        label.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(label)
        widget = MatrixWidget(self.W0)
        v_layout.addWidget(widget)
        h_layout.addLayout(v_layout, 4)

        h_layout.addStretch(3)
        h_container.setLayout(h_layout)

        self.display_layout.addWidget(h_container, 1)
        self.display_layout.addStretch()

        self.info_label.setText("Этап 2 выполнен. Теперь можно запустить финальную волну (Этап 3).")
        self.btn_stage3.setEnabled(True)
        self.btn_stage4.setEnabled(False)

    def start_stage3(self):
        if self.W0 is None:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните Этап 2")
            return
        tau = self.tau_spin.value()
        if tau <= 0:
            QMessageBox.warning(self, "Ошибка", "τ должно быть > 0")
            return
        self.timer_stage3.stop()
        self.final_anim_mat = [row[:] for row in self.W0]
        self.final_anim_step = 0
        self.final_anim_total = tau
        self.clear_layout(self.display_layout)

        self.display_layout.addStretch()

        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.addStretch(3)

        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignCenter)
        label = QLabel(f"Финальная волна (шаг 0 из {tau})")
        label.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(label)
        self.final_widget = MatrixWidget(self.final_anim_mat)
        v_layout.addWidget(self.final_widget)
        h_layout.addLayout(v_layout, 4)

        h_layout.addStretch(3)
        h_container.setLayout(h_layout)

        self.display_layout.addWidget(h_container, 1)
        self.display_layout.addStretch()

        self.timer_stage3.start(300)
        self.btn_stage3.setEnabled(False)
        self.btn_stage2.setEnabled(False)
        self.btn_stage4.setEnabled(False)
        self.info_label.setText("Анимация финальной волны...")

    def do_final_wave_step(self):
        if self.final_anim_step >= self.final_anim_total:
            self.timer_stage3.stop()
            self.info_label.setText("Готово. Кратчайший путь до выхода найден.")
            self.btn_stage2.setEnabled(True)
            self.btn_stage3.setEnabled(True)
            self.btn_stage4.setEnabled(True)   # Активируем кнопку для построения пути
            return
        self.propagate_one_step(self.final_anim_mat, self.final_anim_step)
        self.final_widget.update()
        for child in self.display_widget.findChildren(QLabel):
            if "Финальная волна" in child.text():
                child.setText(f"Финальная волна (шаг {self.final_anim_step+1} из {self.final_anim_total})")
                break
        self.final_anim_step += 1

    def show_full_path(self):
        """Этап 4: построить и отобразить путь от стартовой точки до выхода."""
        if self.W0 is None:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните этапы 1–3.")
            return
        if not self.stage_matrices:
            QMessageBox.warning(self, "Ошибка", "Нет данных о выходах.")
            return

        walls = self.matrices[0]
        path_to_W0 = bfs_to_W0(self.start_point, self.W0, walls)
        if path_to_W0 is None:
            QMessageBox.information(self, "Инфо", "Нет пути от старта до области W0.")
            return

        last_cell = path_to_W0[-1]
        p = self.p_spin.value()
        tau = self.tau_spin.value()
        max_steps = p - tau
        exit_cell = find_exit_cell(last_cell, self.stage_matrices, max_steps)
        if exit_cell is None:
            QMessageBox.information(self, "Инфо", f"Нет выхода, достижимого из W0 за {max_steps} шагов.")
            return

        # Находим матрицу расстояний, соответствующую найденному выходу
        dist_matrix = None
        for mat in self.stage_matrices:
            if mat[exit_cell[1]][exit_cell[0]] == 0:
                dist_matrix = mat
                break
        if dist_matrix is None:
            QMessageBox.warning(self, "Ошибка", "Не найдена матрица расстояний для выхода.")
            return

        # ВОТ ЭТА СТРОКА БЫЛА ПРОПУЩЕНА
        path_to_exit = build_path_to_exit(last_cell, exit_cell, dist_matrix)
        if path_to_exit is None:
            QMessageBox.information(self, "Инфо", "Не удалось восстановить путь до выхода.")
            return

        full_path = path_to_W0 + path_to_exit[1:]
        self._display_path(full_path)

    def _display_path(self, path):
        rows, cols = len(self.W0), len(self.W0[0])
        display_mat = [[-1]*cols for _ in range(rows)]
        walls = self.matrices[0]
        for y in range(rows):
            for x in range(cols):
                if walls[y][x] == -2:
                    display_mat[y][x] = -2
        for (x, y) in path:
            if display_mat[y][x] != -2:
                display_mat[y][x] = 5  # путь
        sx, sy = path[0]
        ex, ey = path[-1]
        display_mat[sy][sx] = 6  # старт
        display_mat[ey][ex] = 7  # выход

        self.clear_layout(self.display_layout)
        self.display_layout.addStretch()

        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.addStretch(3)

        class PathMatrixWidget(MatrixWidget):
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                rows = len(self.matrix)
                cols = len(self.matrix[0])
                w = self.width()
                h = self.height()
                if w == 0 or h == 0:
                    return
                cell_w = w / cols
                cell_h = h / rows
                cell_size = min(cell_w, cell_h)
                offset_x = (w - cell_size * cols) / 2
                offset_y = (h - cell_size * rows) / 2
                for i in range(rows):
                    for j in range(cols):
                        rect = QRectF(offset_x + j * cell_size, offset_y + i * cell_size, cell_size, cell_size)
                        val = self.matrix[i][j]
                        if val == -2:
                            painter.fillRect(rect, QColor(80, 80, 80))
                        elif val == -1:
                            painter.fillRect(rect, QColor(240, 240, 240))
                        elif val == 5:
                            painter.fillRect(rect, QColor(0, 100, 200))
                        elif val == 6:
                            painter.fillRect(rect, QColor(0, 255, 0))
                        elif val == 7:
                            painter.fillRect(rect, QColor(255, 0, 0))
                        else:
                            painter.fillRect(rect, QColor(200, 200, 200))
                        painter.drawRect(rect)

        widget = PathMatrixWidget(display_mat)
        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignCenter)
        label = QLabel("Полный путь от старта до выхода (синий)")
        label.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(label)
        v_layout.addWidget(widget)
        h_layout.addLayout(v_layout, 4)
        h_layout.addStretch(3)
        h_container.setLayout(h_layout)

        self.display_layout.addWidget(h_container, 1)
        self.display_layout.addStretch()

        self.info_label.setText(f"Путь построен. Длина: {len(path)} шагов. Старт: {path[0]}, выход: {path[-1]}.")
        self.btn_stage4.setEnabled(False)  # отключаем после построения

    def load_matrices(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Выберите карты для каждого выхода", "", "Text files (*.txt)"
        )
        if len(filenames) < 2:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы 2 карты!")
            return
        self.matrices = []
        for fname in filenames:
            try:
                m = read_file(fname)
                self.matrices.append(m)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать {fname}: {e}")
                return
        self.stage_matrices = []
        self.W0 = None
        self.timer_stage1.stop()
        self.timer_stage3.stop()
        self.clear_layout(self.display_layout)

        self.display_layout.addStretch()

        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setSpacing(15)
        h_layout.addStretch(3)

        for idx, mat in enumerate(self.matrices):
            col_layout = QVBoxLayout()
            col_layout.setAlignment(Qt.AlignCenter)
            label = QLabel(f"Исходная карта выхода {idx+1}")
            label.setAlignment(Qt.AlignCenter)
            col_layout.addWidget(label)
            widget = MatrixWidget(mat)
            col_layout.addWidget(widget)
            h_layout.addLayout(col_layout, 4)

        h_layout.addStretch(3)
        h_container.setLayout(h_layout)

        self.display_layout.addWidget(h_container, 1)
        self.display_layout.addStretch()

        self.info_label.setText(f"Загружено {len(self.matrices)} карт. Старт: (0,0). Нажмите 'Этап 1'.")
        self.btn_stage1.setEnabled(True)
        self.btn_stage2.setEnabled(False)
        self.btn_stage3.setEnabled(False)
        self.btn_stage4.setEnabled(False)