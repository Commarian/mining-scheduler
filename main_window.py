# main_window.py
import pandas as pd

import PyQt5.QtWidgets as q
from PyQt5 import QtGui

from new_issue_list_window import NewIssueListWindow
from firebase_manager import FirebaseManager
from table_model import TableModel


class MainWindow(q.QMainWindow):
    def __init__(self):
        super().__init__()

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
        data = [
            [4, 9, 2],
            [1, 0, 0],
            [3, 5, 0],
            [3, 3, 2],
            [7, 8, 9],
        ]
        model = TableModel(data)
        table.setModel(model)
        self.setCentralWidget(table)

        layout = q.QVBoxLayout(self)

        layout.addWidget(new_jobcard_button)
        layout.addWidget(new_issue_list_button)
        layout.addWidget(import_csv_button)
        layout.addWidget(exit_button)
        layout.addWidget(table)
        self.setLayout(layout)

    def show_new_issue_list_window(self):
        if not self.new_issue_list_window:
            self.new_issue_list_window = NewIssueListWindow(self.firebase_manager)
        self.new_issue_list_window.show()







