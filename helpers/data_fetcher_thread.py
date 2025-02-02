# data_fetcher_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class DataFetcherThread(QThread):
    finished_fetching = pyqtSignal()

    def run(self):
        # This is a synchronous call but runs in a separate thread
        statics.firebase_manager.set_issues()
        self.finished_fetching.emit()