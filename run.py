from PyQt6.QtWidgets import QApplication

from system import System
import sys


if __name__ == '__main__':
    app = QApplication([])

    system = System()
    system.show()

    sys.exit(app.exec())