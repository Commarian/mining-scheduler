from PyQt5.QtCore import QThread, pyqtSignal


class MultiThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, firebase_manager):
        super(MultiThread, self).__init__()
        self.firebase_manager = firebase_manager

    def run(self):
        self.firebase_manager.set_issues()
        self.finished_signal.emit()