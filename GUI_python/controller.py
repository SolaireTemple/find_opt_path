import json
import os
import sys
from pathlib import Path
import shutil

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QScrollArea, QLabel, QComboBox
)

from maze_editor import MazeEditor
from obstacle_editor import ObstacleEditor
from config_manager import generate_config_file, delete_config_file, load_config_file
from visualizer import Visualizer
from multiple_exits_widget import MultipleExitsWidget

def find_cpp_exe():
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "../find_opt_path/x64/Release/find_opt_path.exe",
        base_dir / "../find_opt_path/Release/find_opt_path.exe",
        base_dir / "../find_opt_path/x64/Debug/find_opt_path.exe",
        base_dir / "../find_opt_path/Debug/find_opt_path.exe",
        base_dir / "find_opt_path.exe",
        base_dir / "../x64/Release/find_opt_path.exe",
    ]
    for path in candidates:
        if path.exists():
            return str(path.resolve())
    return None


class Controller(QMainWindow):
    def __init__(self, maze_size=8):
        super().__init__()
        self.maze_size = maze_size
        self.setWindowTitle("Maze Path Visualizer")
        self.setMinimumSize(1000, 800)

        self.cpp_exe = find_cpp_exe()
        if self.cpp_exe is None:
            QMessageBox.critical(self, "Ошибка",
                                 "Не найден исполняемый файл find_opt_path.exe.\n"
                                 "Убедитесь, что проект C++ скомпилирован (Release).")
            sys.exit(1)
        else:
            print(f"Найден C++ executable: {self.cpp_exe}")

        self.setup_ui()
        self.cpp_process = None

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Внешний таббар для двух задач
        main_tabs = QTabWidget()

        # --- Вкладка "Задача 1: Движущееся препятствие" ---
        task1_widget = QWidget()
        task1_layout = QVBoxLayout(task1_widget)

        # Внутренний таббар для задачи 1
        self.tabs_task1 = QTabWidget()

        # Вкладка "Лабиринт" с выбором размера
        maze_tab = self._create_maze_tab_with_resize()
        self.tabs_task1.addTab(maze_tab, "Лабиринт")

        # Вкладка "Препятствие"
        self.obstacle_editor = ObstacleEditor(size=self.maze_size)
        self.scroll_obs = QScrollArea()
        self.scroll_obs.setWidget(self.obstacle_editor)
        self.scroll_obs.setWidgetResizable(True)
        self.tabs_task1.addTab(self.scroll_obs, "Препятствие")

        # Вкладка "Анимация"
        self.visualizer = Visualizer(size=self.maze_size)
        self.scroll_viz = QScrollArea()
        self.scroll_viz.setWidget(self.visualizer)
        self.scroll_viz.setWidgetResizable(True)
        self.tabs_task1.addTab(self.scroll_viz, "Анимация")

        # Синхронизация лабиринта с редактором препятствия
        def update_obstacle_maze():
            walls = self.maze_editor.get_walls_matrix()
            start = self.maze_editor.get_start()
            exit_ = self.maze_editor.get_exit()
            self.obstacle_editor.update_maze_data(walls, start, exit_)

        update_obstacle_maze()
        self.maze_editor.data_changed.connect(update_obstacle_maze)

        task1_layout.addWidget(self.tabs_task1)
        task1_widget.setLayout(task1_layout)
        main_tabs.addTab(task1_widget, "Задача 1: Движущееся препятствие")

        # --- Вкладка "Задача 2: Неизвестные выходы" ---
        self.task2_widget = MultipleExitsWidget(size=self.maze_size)
        main_tabs.addTab(self.task2_widget, "Задача 2: Неизвестные выходы")

        main_layout.addWidget(main_tabs)

    def _create_maze_tab_with_resize(self):
        """Создаёт вкладку лабиринта с возможностью изменения размера."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Редактор лабиринта
        self.maze_editor = MazeEditor(size=self.maze_size)
        self.scroll_maze = QScrollArea()
        self.scroll_maze.setWidget(self.maze_editor)
        self.scroll_maze.setWidgetResizable(True)
        layout.addWidget(self.scroll_maze)

        # Панель для выбора размера
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Размер лабиринта (степень двойки):"))
        self.size_combo = QComboBox()
        sizes = ["4", "8", "16", "32", "64"]
        self.size_combo.addItems(sizes)
        self.size_combo.setCurrentText(str(self.maze_size))
        size_layout.addWidget(self.size_combo)
        self.apply_size_btn = QPushButton("Применить размер")
        self.apply_size_btn.clicked.connect(self.on_apply_size)
        size_layout.addWidget(self.apply_size_btn)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # Панель основных кнопок (загрузить, сохранить, найти путь)
        btn_layout = QHBoxLayout()
        self.load_config_btn = QPushButton("Загрузить конфиг")
        self.load_config_btn.setMinimumWidth(100)
        self.save_config_btn = QPushButton("Сохранить конфиг")
        self.save_config_btn.setMinimumWidth(100)
        self.find_path_btn = QPushButton("Найти путь")
        self.find_path_btn.setMinimumWidth(100)

        self.load_config_btn.clicked.connect(self.load_config_file)
        self.save_config_btn.clicked.connect(self.save_config_file)
        self.find_path_btn.clicked.connect(self.run_cpp)

        btn_layout.addWidget(self.load_config_btn)
        btn_layout.addWidget(self.save_config_btn)
        btn_layout.addWidget(self.find_path_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab_widget

    def change_maze_size(self, new_size, ask_confirmation=False):
        """Изменяет размер лабиринта и пересоздаёт связанные виджеты."""
        if new_size == self.maze_size:
            return True
        if ask_confirmation:
            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Изменить размер лабиринта на {new_size}x{new_size}?\n"
                                         "Текущие данные будут сброшены.",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return False
        # Обновляем размер
        self.maze_size = new_size
        # Пересоздаём редактор лабиринта
        old_maze = self.maze_editor
        self.maze_editor = MazeEditor(size=self.maze_size)
        self.scroll_maze.takeWidget()
        self.scroll_maze.setWidget(self.maze_editor)
        old_maze.deleteLater()
        # Пересоздаём редактор препятствия
        old_obs = self.obstacle_editor
        self.obstacle_editor = ObstacleEditor(size=self.maze_size)
        self.scroll_obs.takeWidget()
        self.scroll_obs.setWidget(self.obstacle_editor)
        old_obs.deleteLater()
        # Пересоздаём визуализатор
        old_viz = self.visualizer
        self.visualizer = Visualizer(size=self.maze_size)
        self.scroll_viz.takeWidget()
        self.scroll_viz.setWidget(self.visualizer)
        old_viz.deleteLater()
        # Синхронизация
        def update_obstacle_maze():
            walls = self.maze_editor.get_walls_matrix()
            start = self.maze_editor.get_start()
            exit_ = self.maze_editor.get_exit()
            self.obstacle_editor.update_maze_data(walls, start, exit_)
        update_obstacle_maze()
        self.maze_editor.data_changed.connect(update_obstacle_maze)
        # Обновляем комбобокс (если он существует)
        if hasattr(self, 'size_combo'):
            self.size_combo.setCurrentText(str(self.maze_size))
        self.statusBar().showMessage(f"Размер лабиринта изменён на {self.maze_size}x{self.maze_size}")
        return True

    def on_apply_size(self):
        """Обработчик нажатия кнопки 'Применить размер'."""
        new_size = int(self.size_combo.currentText())
        self.change_maze_size(new_size, ask_confirmation=True)

    def load_config_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить конфигурацию", "", "Text files (*.txt)")
        if not filename:
            return
        try:
            # Сначала прочитаем размер из файла, чтобы при необходимости изменить размер виджетов
            with open(filename, 'r') as f:
                lines = f.readlines()
            size_in_file = None
            for line in lines:
                if line.startswith("size"):
                    size_in_file = int(line.split()[1])
                    break
            if size_in_file is not None and size_in_file != self.maze_size:
                # Автоматически меняем размер (без подтверждения, так как пользователь загружает конфиг)
                self.change_maze_size(size_in_file, ask_confirmation=False)
            # Теперь загружаем остальные параметры
            load_config_file(filename, self.maze_editor, self.obstacle_editor)
            QMessageBox.information(self, "Успех", "Конфигурация загружена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию:\n{e}")

    def save_config_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить конфигурацию", "", "Text files (*.txt)")
        if filename:
            path = generate_config_file(self.maze_editor, self.obstacle_editor)
            shutil.copy(path, filename)
            delete_config_file(path)
            QMessageBox.information(self, "Info", f"Конфигурация сохранена в {filename}")

    def run_cpp(self):
        config_path = generate_config_file(self.maze_editor, self.obstacle_editor)
        self.cpp_process = QProcess()
        self.cpp_process.finished.connect(lambda code, status: self.on_cpp_finished(config_path, code))
        self.cpp_process.start(self.cpp_exe, [config_path])
        self.find_path_btn.setEnabled(False)
        self.statusBar().showMessage("Поиск пути...")

    def on_cpp_finished(self, config_path, exit_code):
        delete_config_file(config_path)
        self.find_path_btn.setEnabled(True)
        if exit_code != 0:
            self.statusBar().showMessage("Ошибка C++ программы")
            err = self.cpp_process.readAllStandardError().data().decode()
            QMessageBox.critical(self, "Ошибка", f"Код ошибки: {exit_code}\n{err}")
            return
        output = self.cpp_process.readAllStandardOutput().data().decode()
        try:
            data = json.loads(output)
            path = [(p['x'], p['y'], p['t']) for p in data.get('path', [])]
            if not path:
                self.statusBar().showMessage("Путь не найден")
                QMessageBox.information(self, "Информация", "Путь не найден!")
                return
            obstacle_frames = data.get('obstacle_positions', [])
            walls = self.maze_editor.get_walls_matrix()
            self.visualizer.set_data(path, obstacle_frames, walls)
            self.visualizer.start_animation()
            self.statusBar().showMessage(f"Путь найден, время выхода: {path[-1][2]}")
            # Переключаем внутренний таббар задачи 1 на вкладку анимации (индекс 2)
            if hasattr(self, 'tabs_task1'):
                self.tabs_task1.setCurrentIndex(2)
            else:
                tabs = self.centralWidget().findChild(QTabWidget)
                if tabs:
                    tabs.setCurrentIndex(2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать JSON:\n{e}\n{output}")