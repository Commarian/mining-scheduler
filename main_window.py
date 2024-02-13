# main_window.py
import pandas as pd

import PyQt6.QtWidgets as q
from PyQt6 import QtGui

from new_issue_list_window import NewIssueListWindow
from firebase_manager import FirebaseManager
from table_model import TableModel


class MainWindow(q.QWidget):
    def __init__(self):
        super().__init__()

        headers = ['End Date', 'Originator', 'Start Date', 'Hazard', 'Source', 'Hazard Classification', 'Rectification',
                   'Location', 'Priority', 'Person Responsible']
        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 800, 800)

        # Initialize FirebaseManager with the path to the service account key
        self.firebase_manager = FirebaseManager()
        self.firebase_manager.set_issues()


        self.new_jobcard_window = None
        self.new_issue_list_window = None

        new_jobcard_button = q.QPushButton("New Jobcard", self)


        new_issue_list_button = q.QPushButton("New Issue List", self)
        new_issue_list_button.clicked.connect(self.show_new_issue_list_window)

        exit_button = q.QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)

        import_csv_button = q.QPushButton("Import CSV", self)
        #import_csv_button.clicked.connect(self.import_and_upload_csv)

        #Table
        table = q.QTableView()
        data = self.convert_issues_to_data()
        model = TableModel(data, headers)
        table.setModel(model)
        #self.setCentralWidget(table)

        layoutV = q.QVBoxLayout(self)

        layoutV.addWidget(new_jobcard_button)
        layoutV.addWidget(new_issue_list_button)
        layoutV.addWidget(import_csv_button)
        layoutV.addWidget(exit_button)


        layoutH = q.QHBoxLayout(self)
        layoutV.addChildLayout(layoutH)
        layoutH.addWidget(table)

        self.setLayout(layoutV)

    def show_new_issue_list_window(self):
        if not self.new_issue_list_window:
            self.new_issue_list_window = NewIssueListWindow(self.firebase_manager)
        self.new_issue_list_window.show()

    def convert_issues_to_data(self):
        data = []
        issues = self.firebase_manager.issues_hash
        id_list = self.firebase_manager.id_list

        for int in range(len(id_list)):
            data.append(list(issues.get_val(id_list[int]).values()))
        print("data = "+str(data))
        return data







