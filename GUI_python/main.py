import sys
from PySide6.QtWidgets import QApplication
from controller import Controller

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Controller()          # размер по умолчанию 8
    window.show()
    sys.exit(app.exec())