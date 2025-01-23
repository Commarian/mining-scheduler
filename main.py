import os
import sys

import firebase_admin
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from auth_window import AuthWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    #main_window = MainWindow()

    #main_window.show()
    sys.exit(app.exec())
