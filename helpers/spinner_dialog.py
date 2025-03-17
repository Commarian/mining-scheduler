# helpers/spinner_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
import statics

class SpinnerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.setWindowTitle("Loading...")

        layout = QVBoxLayout(self)
        self.label = QLabel("Loading, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        # (0, 0) => indefinite / busy mode
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
