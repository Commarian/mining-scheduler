# loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
from main_window import MainWindow

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super(LoadingDialog, self).__init__(parent)
        self.setWindowTitle("Loading Data")
        # Remove window frame for a splash-screen look:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)
        # A label with a cool message (you can customize the font and color via stylesheet)
        self.label = QLabel("Fetching data...\nPlease wait.", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # An indefinite progress bar (ranges 0 to 0 show busy state)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        #TODO fix this with progress real
        self.open_main_window()
        
    def open_main_window(self):
        """
        Launch the main window upon success.
        """
        main_window = MainWindow()
        main_window.show()
        
