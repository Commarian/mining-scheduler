import sys

from PyQt5.QtWidgets import QApplication

from auth_window import AuthWindow
from main_window import MainWindow
from firebase_manager import FirebaseManager
import statics

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Instantiate FirebaseManager and store it for use throughout the app.
    statics.firebase_manager = FirebaseManager()
    auth_window = AuthWindow() #this is the real way of calling it
    auth_window.show() #this is the real way of calling it
    #for testing use:
    #MainWindow().show()


    sys.exit(app.exec())
