# new_issue_list_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit

class NewIssueListWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):
        self.issue_title_label = QLabel("Issue Title:")
        self.issue_title_entry = QLineEdit()

        self.category_label = QLabel("Category:")
        self.category_dropdown = QComboBox()
        self.populate_dropdown(self.category_dropdown, ["Category A", "Category B", "Category C"])

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, ["High", "Medium", "Low"])

        self.issue_description_label = QLabel("Issue Description:")
        self.issue_description_entry = QTextEdit()

        save_button = QPushButton("Save Issue", self)
        save_button.clicked.connect(self.save_issue)

        layout = QVBoxLayout(self)
        layout.addWidget(self.issue_title_label)
        layout.addWidget(self.issue_title_entry)
        layout.addWidget(self.category_label)
        layout.addWidget(self.category_dropdown)
        layout.addWidget(self.priority_label)
        layout.addWidget(self.priority_dropdown)
        layout.addWidget(self.issue_description_label)
        layout.addWidget(self.issue_description_entry)
        layout.addWidget(save_button)

    def populate_dropdown(self, dropdown, items):
        dropdown.addItems(items)

    def save_issue(self):
        title = self.issue_title_entry.text()
        category = self.category_dropdown.currentText()
        priority = self.priority_dropdown.currentText()
        issue_description = self.issue_description_entry.toPlainText()

        # Add logic to save issue details (you can use Firebase here)

        print(f"Issue Title: {title}")
        print(f"Category: {category}")
        print(f"Priority: {priority}")
        print(f"Issue Description: {issue_description}")

        # You can emit a signal to update the main window or do other actions here
