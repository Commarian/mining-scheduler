import os

import firebase_admin
from PyQt5.QtCore import QThread, pyqtSignal
from firebase_admin import credentials, firestore
from msal import PublicClientApplication

import statics
from firebase_manager import FirebaseManager


class MultiThread(QThread):
    finished_signal = pyqtSignal()  # Signal to indicate completion

    def __init__(self, method):
        super(MultiThread, self).__init__()

        # Create a self-invoking lambda to avoid issues with method execution
        self.task = lambda: method()

    def run(self):
        self.task()  # Execute the passed method within the thread
        self.finished_signal.emit()  # Emit signal after task is complete
