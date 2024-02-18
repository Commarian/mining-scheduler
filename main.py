import os
import sys

from flask import Flask, request, redirect, session
import firebase_admin
import msal
from PyQt5.QtWidgets import QApplication
from firebase_admin import auth
from flask import session, redirect, request
from msal import PublicClientApplication

import statics
from main_window import MainWindow
from sign_in_dialog import SignInDialog

import wmi


import getpass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    c = wmi.WMI()
    for account in c.Win32_UserAccount():
        if account.SIDType == 1:  # Focus on user accounts
            print("Name:", account.Name)
    script_dir = os.path.dirname(__file__)
    json_path = os.path.join(script_dir, "firebaseadminsdk.json")
    # Initialize Firebase with offline persistence
    cred = firebase_admin.credentials.Certificate(json_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://job-card.firebaseio.com',
    }, name='issues_app')
    print("Initializing Firebase Manager")

    main_window = MainWindow()


    main_window.show()
    sys.exit(app.exec())





    #SecretID
    #935eda0c-b184-472a-8b36-bf037d93a4ee
    #SecretValue
    #rtI8Q~N86CYSwBxD~JG4Y_o9djhy-O81CitEba6x
