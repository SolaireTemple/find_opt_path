import json
import os
import sys
from pathlib import Path
import shutil

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QScrollArea
)

from maze_editor import MazeEditor
from obstacle_editor import ObstacleEditor
from config_manager import generate_config_file, delete_config_file
from visualizer import Visualizer

def find_cpp_exe():
    """
    Ищет find_opt_path.exe в папках:
        - относительно расположения этого скрипта
        - внутри папки find_opt_path (проект C++)
    Возвращает абсолютный путь к exe или None, если не найден.
    """
    # Директория, где лежит controller.py
    base_dir = Path(__file__).resolve().parent

    # Список возможных относительных путей (наиболее вероятные первыми)
    candidates = []

    # 1. Стандартный путь для Visual Studio (x64 Release)
    candidates.append(base_dir / "../find_opt_path/x64/Release/find_opt_path.exe")
    # 2. 32-битная сборка (Win32 или x86)
    candidates.append(base_dir / "../find_opt_path/Win32/Release/find_opt_path.exe")
    candidates.append(base_dir / "../find_opt_path/x86/Release/find_opt_path.exe")
    # 3. Без указания платформы (Release)
    candidates.append(base_dir / "../find_opt_path/Release/find_opt_path.exe")
    # 4. Debug версии
    candidates.append(base_dir / "../find_opt_path/x64/Debug/find_opt_path.exe")
    candidates.append(base_dir / "../find_opt_path/Debug/find_opt_path.exe")
    # 5. Прямо в папке с Python (если скопировали)
    candidates.append(base_dir / "find_opt_path.exe")
    # 6. В папке выше (если Python запускается из корня репозитория)
    candidates.append(base_dir / "../find_opt_path.exe")

    # Проверяем каждый возможный путь
    for path in candidates:
        if path.exists():
            return str(path.resolve())

    # Если не нашли, ищем рекурсивно в папке find_opt_path
    proj_dir = base_dir / "../find_opt_path"
    if proj_dir.exists():
        for exe in proj_dir.rglob("find_opt_path.exe"):
            return str(exe.resolve())

    return None


class Controller(QMainWindow):
    def __init__(self, maze_size=8):
        super().__init__()
        self.maze_size = maze_size
        self.setWindowTitle("Maze Path Visualizer with Dynamic Obstacle")
        self.setMinimumSize(900, 700)
        # Поиск exe
        self.cpp_exe = find_cpp_exe()
        if self.cpp_exe is None:
            QMessageBox.critical(self, "Ошибка",
                                 "Не найден исполняемый файл find_opt_path.exe.\n"
                                 "Убедитесь, что проект C++ скомпилирован (Release) и находится в папке ../find_opt_path/\n"
                                 "Или скопируйте exe в папку с Python скриптом.")
            sys.exit(1)
        else:
            print(f"Найден C++ executable: {self.cpp_exe}")
        self.setup_ui()
        self.cpp_process = None

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tabs = QTabWidget()

        # Вкладка "Лабиринт" (с кнопками)
        maze_tab = self._create_maze_tab()
        tabs.addTab(maze_tab, "Лабиринт")

        # Вкладка "Препятствие"
        self.obstacle_editor = ObstacleEditor(size=self.maze_size)
        scroll_obs = QScrollArea()
        scroll_obs.setWidget(self.obstacle_editor)
        scroll_obs.setWidgetResizable(True)
        tabs.addTab(scroll_obs, "Препятствие")

        # Вкладка "Анимация"
        self.visualizer = Visualizer(size=self.maze_size)
        scroll_viz = QScrollArea()
        scroll_viz.setWidget(self.visualizer)
        scroll_viz.setWidgetResizable(True)
        tabs.addTab(scroll_viz, "Анимация")

        layout.addWidget(tabs)

        # Синхронизация лабиринта с редактором препятствия
        def update_obstacle_maze():
            walls = self.maze_editor.get_walls_matrix()
            start = self.maze_editor.get_start()
            exit_ = self.maze_editor.get_exit()
            self.obstacle_editor.update_maze_data(walls, start, exit_)

        # Начальная синхронизация
        update_obstacle_maze()
        # Подключаем сигнал изменений лабиринта (требуется добавить Signal в MazeEditor)
        self.maze_editor.data_changed.connect(update_obstacle_maze)

    def _create_maze_tab(self):
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Редактор лабиринта
        self.maze_editor = MazeEditor(size=self.maze_size)
        scroll_maze = QScrollArea()
        scroll_maze.setWidget(self.maze_editor)
        scroll_maze.setWidgetResizable(True)
        layout.addWidget(scroll_maze)

        # Панель кнопок
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

    def load_config_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить конфигурацию", "", "Text files (*.txt)")
        if filename:
            try:
                from config_manager import load_config_file as load_config
                load_config(filename, self.maze_editor, self.obstacle_editor)
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
            tabs = self.centralWidget().findChild(QTabWidget)
            if tabs:
                tabs.setCurrentIndex(2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать JSON:\n{e}\n{output}")