import sys

from PyQt5.QtWidgets import QApplication

from auth_window import AuthWindow
from firebase_manager import FirebaseManager
import statics

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Instantiate FirebaseManager and store it for use throughout the app.
    statics.firebase_manager = FirebaseManager()
    auth_window = AuthWindow()
    auth_window.show()

    sys.exit(app.exec())
