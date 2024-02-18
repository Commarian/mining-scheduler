import os

import firebase_admin
from PyQt5.QtCore import QThread, pyqtSignal
from firebase_admin import credentials, firestore
from msal import PublicClientApplication

import statics


class MultiThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self):
        super(MultiThread, self).__init__()


    def run(self):
        # Azure AD Tenant, Client ID, and Client Secret




        self.finished_signal.emit()