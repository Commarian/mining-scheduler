from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
import statics

class AddRecordLoadingDialog(QDialog):
    """
    Simple 'Loading...' dialog for the Add Record flow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.setWindowTitle("Loading...")

        layout = QVBoxLayout(self)
        self.label = QLabel("Loading record data, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # A progress bar with no real progress metric (just indefinite)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)   # 0,0 => 'busy indicator'
        layout.addWidget(self.progress_bar)
