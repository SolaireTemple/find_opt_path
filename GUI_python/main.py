import sys
from PySide6.QtWidgets import QApplication, QInputDialog
from controller import Controller

if __name__ == "__main__":
    app = QApplication(sys.argv)
    sizes = ["4", "8", "16", "32", "64"]
    size_str, ok = QInputDialog.getItem(
        None,
        "Размер лабиринта",
        "Выберите размер (степень двойки):",
        sizes,
        1,  # индекс по умолчанию (8)
        False
    )
    if not ok:
        sys.exit(0)
    size = int(size_str)
    window = Controller(maze_size=size)
    window.show()
    sys.exit(app.exec())