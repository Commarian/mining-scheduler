# main_window.py
import sys
import webbrowser


import PyQt5.QtWidgets as q
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from flask import session

import custom_q_pushbutton
import my_table_view
import statics
from multi_thread import MultiThread
from new_issue_list_window import IssueWindow
from firebase_manager import FirebaseManager
from sign_in_dialog import SignInDialog
from table_model import TableModel
import firebase_admin
import os
import msal
from msal import PublicClientApplication


class MainWindow(q.QWidget):
    headers = ['End Date', 'Originator', 'Start Date', 'Hazard', 'Source', 'Hazard Classification', 'Rectification',
               'Location', 'Priority', 'Person Responsible']

    def __init__(self):
        super().__init__()
        # Show the main window only after successful authentication
        # Initialize FirebaseManager with the path to the service account key

        if sys.platform == 'win32' or sys.platform == 'cygwin':  # Covers most Windows setups
            self.do_windows_specific_task()
        else:
            #self.show_authentication_error()
            print("This code block is designed for Windows environments.")

        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 1400, 800)

        self.new_issue_list_window = None

        add_issue_button = custom_q_pushbutton.generate_button("Add Issue")
        add_issue_button.clicked.connect(lambda: self.show_issue_window(True))

        self.update_issue_button = custom_q_pushbutton.generate_button("Update Issue")
        self.update_issue_button.clicked.connect(lambda: self.show_issue_window(False))
        self.update_issue_button.setDisabled(True)

        exit_button = custom_q_pushbutton.generate_button("Exit")
        exit_button.clicked.connect(self.close)

        model = TableModel([], self.headers)
        self.table = my_table_view.MyTableView(model)
        self.table.rowSelected.connect(self.handleRowSelected)

        layout = q.QVBoxLayout(self)

        layout.addWidget(add_issue_button)
        layout.addWidget(self.update_issue_button)
        layout.addWidget(exit_button)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.firebase_manager = FirebaseManager()
        thread = MultiThread(self.firebase_manager.set_issues)
        thread.finished_signal.connect(self.on_thread_finished)
        thread.setParent(self)
        thread.start()

    def show_issue_window(self, is_new_issue):
        self.new_issue_list_window = IssueWindow(self.firebase_manager, is_new_issue).show()

    def convert_issues_to_data(self):
        data = []
        issues = statics.issues_hash
        id_list = statics.id_list

        for int in range(len(id_list)):
            data.append(list(issues.get(id_list[int]).values()))
        print("data = " + str(data))
        return data

    def handleRowSelected(self):
        # Get the selected row number
        selected_index = self.table.selectionModel().currentIndex()
        statics.row_selected = selected_index.row()
        # Implement the desired action when a row is selected
        print("Row selected in main window:", statics.row_selected)
        # Add your custom logic here
        self.update_issue_button.setDisabled(False)

    def on_thread_finished(self):
        print("thread finished")
        # Table
        data = self.convert_issues_to_data()
        model = TableModel(data, self.headers)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()

    def show_authentication_error(self):
        error_message = q.QMessageBox.critical(self, "Authentication Error", "Authentication error. Please sign in to this computer with a valid company account.")
        self.close()  # Close the application on error
        sys.exit()


    def do_windows_specific_task(self):
        # Code that should only run on Windows
        try:
            import wmi
            c = wmi.WMI()
            for account in c.Win32_UserAccount():
                if account.SIDType == 1:  # Focus on user accounts
                    print("Name:", account.Name)
        except Exception as e:
            print(e)
