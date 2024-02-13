from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QDateEdit, \
    QCalendarWidget, QHBoxLayout
from PyQt6.QtCore import QDate, QDateTime, QTime, QRegularExpression

import firebase_manager
import meth


class NewIssueListWindow(QWidget):
    def __init__(self, firebase_manager):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
        self.firebase_manager = firebase_manager
        self.setup_ui()

    def setup_ui(self):
        items = []
        for person in self.firebase_manager.get_data("company_data", "people"):
            items.append(str(person))
        self.person_responsible_label = QLabel("Person Responsible:")
        self.person_responsible_dropdown = QComboBox()
        self.populate_dropdown(self.person_responsible_dropdown, items)
        # TODO remove originator and link to profile signed in
        self.originator_label = QLabel("Originator:")
        self.originator_dropdown = QComboBox()
        self.populate_dropdown(self.originator_dropdown, items)
        items.clear()

        for location in self.firebase_manager.get_data("company_data", "locations"):
            items.append(str(location))
        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, items)

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, ["Class A - LTI", "Class B - MTC", "Class C - FAC"])

        items.clear()
        for location in self.firebase_manager.get_data("company_data", "issue_sources"):
            items.append(str(location))
        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, items)

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"])

        self.start_date_label = QLabel("Start Date:")
        self.start_date_picker = QCalendarWidget()
        self.start_date_picker.setMinimumDate(QDate.currentDate())

        self.duration_days_label = QLabel("Duration days:")
        self.duration_days_text = QLineEdit()
        days_validator = QRegularExpressionValidator(
            QRegularExpression(r"^(?:[1-9][0-9]?|[1-2][0-9]{2}|3[0-5][0-9]|36[0-5])$"))
        self.duration_days_text.setValidator(days_validator)

        self.duration_hours_label = QLabel(" hours:")
        self.duration_hours_text = QLineEdit()
        hours_validator = QRegularExpressionValidator(QRegularExpression(r"^(?:[0-1]?[0-9]|2[0-3])$"))
        self.duration_hours_text.setValidator(hours_validator)

        self.end_date_label = QLabel("End Date:")
        self.end_date_picker = QCalendarWidget()
        self.end_date_picker.setMinimumDate(QDate.currentDate())

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.rectification_label = QLabel("Rectification:")
        self.rectification_entry = QTextEdit()

        self.save_button = QPushButton("Save Issue", self)

        layout = QVBoxLayout(self)

        # Create a grid layout for labels and widgets
        grid_layout = QVBoxLayout()

        grid_layout.addWidget(self.person_responsible_label)
        grid_layout.addWidget(self.person_responsible_dropdown)

        grid_layout.addWidget(self.originator_label)
        grid_layout.addWidget(self.originator_dropdown)

        grid_layout.addWidget(self.location_label)
        grid_layout.addWidget(self.location_dropdown)

        grid_layout.addWidget(self.hazard_classification_label)
        grid_layout.addWidget(self.hazard_classification_dropdown)

        grid_layout.addWidget(self.source_label)
        grid_layout.addWidget(self.source_dropdown)

        grid_layout.addWidget(self.priority_label)
        grid_layout.addWidget(self.priority_dropdown)

        grid_layout.addWidget(self.start_date_label)
        grid_layout.addWidget(self.start_date_picker)

        grid_layout.addWidget(self.duration_days_label)
        grid_layout.addWidget(self.duration_days_text)

        grid_layout.addWidget(self.duration_hours_label)
        grid_layout.addWidget(self.duration_hours_text)

        grid_layout.addWidget(self.end_date_label)
        grid_layout.addWidget(self.end_date_picker)

        grid_layout.addWidget(self.hazard_label)
        grid_layout.addWidget(self.hazard_entry)

        grid_layout.addWidget(self.rectification_label)
        grid_layout.addWidget(self.rectification_entry)

        layout.addLayout(grid_layout)
        layout.addWidget(self.save_button)

        # Connect signals using lambda functions or functools.partial
        self.start_date_picker.clicked.connect(lambda: self.update_end_date("from_start"))
        self.save_button.clicked.connect(self.save_issue)
        self.end_date_picker.clicked.connect(lambda: self.update_duration("from_end"))
        self.duration_days_text.textEdited.connect(lambda: self.update_end_date("from_duration_days"))
        self.duration_hours_text.textEdited.connect(lambda: self.update_end_date("from_duration_hours"))
        self.priority_dropdown.currentIndexChanged.connect(self.handle_priority_change)

    def populate_dropdown(self, dropdown, items):
        dropdown.addItems(items)

    def save_issue(self):
        data_dict = dict(
            person_responsible=self.person_responsible_dropdown.currentText(),
                         originator=self.originator_dropdown.currentText(),
                         location=self.location_dropdown.currentText(),
                         hazard_classification=self.hazard_classification_dropdown.currentText(),
                         source=self.source_dropdown.currentText(),
                         priority=self.priority_dropdown.currentText(),
                         start_date=self.start_date_picker.selectedDate().toString("yyyy-MM-dd"),
                         end_date=self.end_date_picker.selectedDate().toString("yyyy-MM-dd"),
                         hazard=self.hazard_entry.toPlainText(),
                         rectification=self.rectification_entry.toPlainText())

        self.firebase_manager.save_data("issues",data_dict)


    def update_end_date(self, location):
        start_date = self.start_date_picker.selectedDate()
        self.end_date_picker.setMinimumDate(start_date)

        if location == "from_duration_days":
            if self.duration_days_text.text().isnumeric():
                self.days = int(self.duration_days_text.text())
            else:
                self.days = 0
        elif location == "from_duration_hours":
            if self.duration_hours_text.text().isnumeric():
                self.remaining_hours = int(self.duration_hours_text.text())
            else:
                self.remaining_hours = 0

        if QDateTime.currentDateTime().addSecs(
                meth.convert_time(self.remaining_hours, "hours", "seconds")).date() > start_date:
            start_date = start_date.addDays(1)

        start_date = start_date.addDays(self.days)
        self.end_date_picker.setSelectedDate(start_date)


    def update_duration(self, location=None):
        if location == "from_end":
            self.remaining_hours = 0
            self.days = self.start_date_picker.selectedDate().daysTo(self.end_date_picker.selectedDate())
        self.duration_days_text.setText(str(self.days))
        self.duration_hours_text.setText(str(self.remaining_hours))
        if location == "from_priority":
            self.update_end_date("from_priority")

    def handle_priority_change(self):
        priority = self.priority_dropdown.currentText()
        self.days = 0
        self.remaining_hours = 0
        if priority == "Urgent":
            self.remaining_hours = 6
        elif priority == "High (A)":
            self.days = 1
        elif priority == "Medium (B)":
            self.days = 7
        elif priority == "Low (C)":
            self.days = 14
        self.update_duration("from_priority")
