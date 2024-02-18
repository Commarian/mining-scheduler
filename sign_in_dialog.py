from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout


class SignInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Microsoft Sign-In")

        self.info_label = QLabel("Please sign in with your Microsoft account.")
        self.sign_in_button = QPushButton("Sign In")

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.sign_in_button)
        self.setLayout(layout)
