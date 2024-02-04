from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QDateEdit, \
    QCalendarWidget, QHBoxLayout
from PyQt5.QtCore import QDate

from firebase_manager import FirebaseManager


class NewIssueListWindow(QWidget):
    def __init__(self, firebase_manager):
        super().__init__()
        self.firebase_manager = firebase_manager
        self.setup_ui()

    def setup_ui(self):
        items = []
        for person in self.firebase_manager.get_data("company_data", "people"):
            items.append(str(person))
        self.person_responsible_label = QLabel("Person Responsible:")
        self.person_responsible_dropdown = QComboBox()
        self.populate_dropdown(self.person_responsible_dropdown, items)

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
        self.populate_dropdown(self.hazard_classification_dropdown, ["Class A", "Class B", "Class C"])

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
        self.start_date_picker.clicked.connect(self.update_end_date)

        self.duration_label = QLabel("Duration (days):")
        self.duration_picker = QLineEdit()
        self.duration_picker.textChanged.connect(self.update_end_date)

        self.end_date_label = QLabel("End Date:")
        self.end_date_picker = QCalendarWidget()
        self.end_date_picker.setMinimumDate(QDate.currentDate())
        self.end_date_picker.clicked.connect(self.update_duration)

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.rectification_label = QLabel("Rectification:")
        self.rectification_entry = QTextEdit()

        save_button = QPushButton("Save Issue", self)
        save_button.clicked.connect(self.save_issue)

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

        grid_layout.addWidget(self.duration_label)
        grid_layout.addWidget(self.duration_picker)

        grid_layout.addWidget(self.end_date_label)
        grid_layout.addWidget(self.end_date_picker)

        grid_layout.addWidget(self.hazard_label)
        grid_layout.addWidget(self.hazard_entry)

        grid_layout.addWidget(self.rectification_label)
        grid_layout.addWidget(self.rectification_entry)

        layout.addLayout(grid_layout)
        layout.addWidget(save_button)

    def populate_dropdown(self, dropdown, items):
        dropdown.addItems(items)

    def save_issue(self):
        person_responsible = self.person_responsible_dropdown.currentText()
        originator = self.originator_dropdown.currentText()
        location = self.location_dropdown.currentText()
        hazard_classification = self.hazard_classification_dropdown.currentText()
        source = self.source_dropdown.currentText()
        priority = self.priority_dropdown.currentText()
        start_date = self.start_date_picker.selectedDate().toString("yyyy-MM-dd")
        duration = int(self.duration_picker.text())
        end_date = self.start_date_picker.selectedDate().addDays(duration).toString("yyyy-MM-dd")
        hazard = self.hazard_entry.toPlainText()
        rectification = self.rectification_entry.toPlainText()

        # Add logic to save issue details (you can use Firebase here)

        print(f"Person Responsible: {person_responsible}")
        print(f"Originator: {originator}")
        print(f"Location: {location}")
        print(f"Hazard Classification: {hazard_classification}")
        print(f"Source: {source}")
        print(f"Priority: {priority}")
        print(f"Start Date: {start_date}")
        print(f"Duration: {duration} days")
        print(f"End Date: {end_date}")
        print(f"Hazard: {hazard}")
        print(f"Rectification: {rectification}")

    def update_end_date(self):
        try:
            duration = int(self.duration_picker.text())
            start_date = self.start_date_picker.selectedDate()
            end_date = start_date.addDays(duration)
            self.end_date_picker.setSelectedDate(end_date)
        except ValueError:
            # Handle non-integer input for duration
            pass

    def update_duration(self):
        start_date = self.start_date_picker.selectedDate()
        end_date = self.end_date_picker.selectedDate()
        duration = start_date.daysTo(end_date)
        self.duration_picker.setText(str(duration))

        # You can emit a signal to update the main window or do other actions here
