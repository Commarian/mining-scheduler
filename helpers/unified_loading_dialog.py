from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

import statics

class UnifiedLoadingDialog(QDialog):
    """
    Shows a progress bar and a label for messages.
    We create and start the EverythingThread from here,
    or we let the AuthWindow do that. Up to you.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)

        # No close buttons, etc.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.setWindowTitle("Please wait...")

        layout = QVBoxLayout(self)

        self.label = QLabel("Initializing...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # optional Cancel button if you want the user to abort
        # self.cancel_button = QPushButton("Cancel", self)
        # self.cancel_button.clicked.connect(self.handle_cancel)
        # layout.addWidget(self.cancel_button)

    @pyqtSlot(int)
    def handle_progress_update(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def handle_message_update(self, message):
        self.label.setText(message)

    def handle_cancel(self):
        # if you let user cancel the thread:
        # self.everything_thread.terminate() or some other approach
        self.close()
