import os
import sys

import firebase_admin
from PyQt5.QtWidgets import QApplication

from auth_window import AuthWindow
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #auth_window = AuthWindow() #this is the real way of calling it
    #auth_window.show() #this is the real way of calling it
    #for testing use:
    MainWindow().show()
    sys.exit(app.exec())
