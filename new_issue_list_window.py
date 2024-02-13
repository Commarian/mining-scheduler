from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QDateEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QTime, QRegularExpression

import firebase_manager
import main_window
import meth


class IssueWindow(QWidget):
    def __init__(self, firebase_man):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
        self.firebase_manager = firebase_man
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add Issue")
        self.setGeometry(100, 100, 900, 800)

        # Populate dropdown items
        people_items = [str(person) for person in self.firebase_manager.get_data("company_data", "people")]
        locations_items = [str(location) for location in self.firebase_manager.get_data("company_data", "locations")]
        issue_sources_items = [str(location) for location in
                               self.firebase_manager.get_data("company_data", "issue_sources")]

        # Widgets
        self.person_responsible_label = QLabel("Person Responsible:")
        self.person_responsible_dropdown = QComboBox()
        self.populate_dropdown(self.person_responsible_dropdown, people_items)

        self.originator_label = QLabel("Originator:")
        self.originator_dropdown = QComboBox()
        self.populate_dropdown(self.originator_dropdown,
                               people_items)  # TODO: Remove originator and link to profile signed in
        # TODO or maybe just leave it in and grey it out

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, ["Class A - LTI", "Class B - MTC", "Class C - FAC"])

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"])

        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, issue_sources_items)

        self.start_date_label = QLabel("Start Date:")
        self.start_date_picker = QCalendarWidget()
        self.start_date_picker.setMinimumDate(QDate.currentDate())

        self.duration_days_label = QLabel("Duration days:")
        self.duration_days_text = QLineEdit()
        self.setup_validator(self.duration_days_text, r"^(?:[1-9][0-9]?|[1-2][0-9]{2}|3[0-5][0-9]|36[0-5])$")

        self.duration_hours_label = QLabel(" hours:")
        self.duration_hours_text = QLineEdit()
        self.setup_validator(self.duration_hours_text, r"^(?:[0-1]?[0-9]|2[0-3])$")

        self.end_date_label = QLabel("End Date:")
        self.end_date_picker = QCalendarWidget()
        self.end_date_picker.setMinimumDate(QDate.currentDate())

        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, locations_items)

        self.rectification_label = QLabel("Rectification:")
        self.rectification_entry = QTextEdit()

        self.save_button = QPushButton("Save Issue", self)

        # Layout
        grid_layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.addRow(self.person_responsible_label, self.person_responsible_dropdown)
        form_layout.addRow(self.originator_label, self.originator_dropdown)
        form_layout.addRow(self.location_label, self.location_dropdown)
        form_layout.addRow(self.hazard_label, self.hazard_entry)
        form_layout.addRow(self.hazard_classification_label, self.hazard_classification_dropdown)
        form_layout.addRow(self.priority_label, self.priority_dropdown)
        form_layout.addRow(self.source_label, self.source_dropdown)
        form_layout.addRow(self.start_date_label, self.start_date_picker)

        # Combine duration days and duration hours in a single row
        duration_row_layout = QHBoxLayout()
        duration_row_layout.addWidget(self.duration_days_text)
        duration_row_layout.addWidget(self.duration_hours_label)
        duration_row_layout.addWidget(self.duration_hours_text)

        form_layout.addRow(self.duration_days_label, duration_row_layout)

        form_layout.addRow(self.end_date_label, self.end_date_picker)

        form_layout.addRow(self.rectification_label, self.rectification_entry)

        grid_layout.addLayout(form_layout)
        grid_layout.addWidget(self.save_button)
        self.setLayout(grid_layout)

        # Connect signals
        self.start_date_picker.clicked.connect(lambda: self.update_end_date("from_start"))
        self.save_button.clicked.connect(self.save_issue)
        self.end_date_picker.clicked.connect(lambda: self.update_duration("from_end"))
        self.duration_days_text.textEdited.connect(lambda: self.update_end_date("from_duration_days"))
        self.duration_hours_text.textEdited.connect(lambda: self.update_end_date("from_duration_hours"))
        self.priority_dropdown.currentIndexChanged.connect(self.handle_priority_change)

    def populate_dropdown(self, dropdown, items):
        dropdown.addItems(items)

    def setup_validator(self, line_edit, regex):
        validator = QRegularExpressionValidator(QRegularExpression(regex))
        line_edit.setValidator(validator)

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

        self.firebase_manager.save_data("issues", data_dict)

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

    def refresh_data(self, issue_action, issue_action_new):
        if not issue_action_new:
            self.setWindowTitle(issue_action)
