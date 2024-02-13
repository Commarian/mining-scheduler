# main_window.py
import pandas as pd

import PyQt5.QtWidgets as q
from PyQt5 import QtGui

import my_table_view
from new_issue_list_window import IssueWindow
from firebase_manager import FirebaseManager
from table_model import TableModel

class MainWindow(q.QWidget):
    issue_action = "New Issue"
    issue_action_new = True
    def __init__(self):
        super().__init__()

        headers = ['End Date', 'Originator', 'Start Date', 'Hazard', 'Source', 'Hazard Classification', 'Rectification',
                   'Location', 'Priority', 'Person Responsible']
        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize FirebaseManager with the path to the service account key
        self.firebase_manager = FirebaseManager()
        self.firebase_manager.set_issues()

        self.new_jobcard_window = None
        self.new_issue_list_window = None

        self.issue_button = q.QPushButton(self.issue_action)
        self.issue_button.clicked.connect(self.show_issue_window)

        exit_button = q.QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)

        # Table
        data = self.convert_issues_to_data()
        model = TableModel(data, headers)
        table = my_table_view.MyTableView(model)
        table.rowSelected.connect(self.handleRowSelected)

        layout = q.QVBoxLayout(self)

        layout.addWidget(self.issue_button)
        layout.addWidget(exit_button)
        layout.addWidget(table)

        self.setLayout(layout)

    def show_issue_window(self):
        if not self.new_issue_list_window:
            self.new_issue_list_window = IssueWindow(self.firebase_manager)
        self.new_issue_list_window.show()
        self.new_issue_list_window.activateWindow()
        self.new_issue_list_window.refresh_data(self.issue_action, self.issue_action_new)

    def convert_issues_to_data(self):
        data = []
        issues = self.firebase_manager.issues_hash
        id_list = self.firebase_manager.id_list

        for int in range(len(id_list)):
            data.append(list(issues.get_val(id_list[int]).values()))
        print("data = " + str(data))
        return data

    def handleRowSelected(self, selected_row):
        # Implement the desired action when a row is selected
        print("Row selected in main window:", selected_row)
        # Add your custom logic here
        self.issue_action = "Update Issue"
        self.issue_action_new = False
        self.issue_button.setText(self.issue_action)
        self.new_issue_list_window.refresh_data(self.issue_action, self.issue_action_new)
