from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from main_window import MainWindow
import statics




class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super(LoadingDialog, self).__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)
        self.setWindowTitle("Loading Data")
        # Remove window frame for a splash-screen look
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)
        self.label = QLabel("Fetching data...\nPlease wait.", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Set up a progress bar that goes from 0 to 300 (milliseconds)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 300)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Timer for progress updates: update every 5ms
        self.timer = QTimer(self)
        self.timer.setInterval(5)  # 5ms interval
        self.timer.timeout.connect(self.update_progress)

        self.max_progress = 700  # progress bar maximum value (300ms)
        self.progress_value = 0
        self.attempt_count = 0
        self.max_attempts = 10

        self.timer.start()

    def update_progress(self):
        self.progress_value += 1
        if self.progress_value > self.max_progress:
            self.progress_value = self.max_progress
        self.progress_bar.setValue(self.progress_value)

        # When the progress bar is full, check if data is ready.
        if self.progress_value >= self.max_progress:
            if statics.init_loading_done:
                # Data is loaded: stop the timer and open the main window.
                self.timer.stop()
                self.open_main_window()
            else:
                # Data not ready: increment attempt count.
                self.attempt_count += 1
                if self.attempt_count < self.max_attempts:
                    # Reset the progress bar and try again.
                    self.progress_value = 0
                    self.progress_bar.setValue(self.progress_value)
                else:
                    self.timer.stop()
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Unable to load data from Firebase after several attempts."
                    )
                    self.close()

    def open_main_window(self):
        main_window = MainWindow()
        main_window.show()
        self.close()

    def complete_loading(self):
        statics.init_loading_done = True