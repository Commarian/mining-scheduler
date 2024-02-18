from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QDateEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QTime, QRegularExpression, Qt

import custom_q_pushbutton
import firebase_manager
import main_window
import meth
import statics


class IssueWindow(QWidget):
    def __init__(self, firebase_man, is_new_issue):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
        self.firebase_manager = firebase_man
        self.setup_ui(is_new_issue)

    def setup_ui(self, is_new_issue):

        self.setWindowTitle("Add Issue")
        self.setGeometry(100, 100, 900, 800)

        # Populate dropdown items
        people_items = []
        issue_sources_items = []
        locations_items = []
        priority_items = []
        update_end_date = QDate.currentDate()
        if is_new_issue:
            priority_items = ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"]
            people_items = [str(person) for person in self.firebase_manager.get_data("company_data", "people")]
            locations_items = [str(location) for location in self.firebase_manager.get_data("company_data", "locations")]
            issue_sources_items = [str(location) for location in
                                   self.firebase_manager.get_data("company_data", "issue_sources")]
        else:
            if len(statics.id_list) > 0 and statics.row_selected is not None:
                selected_row = statics.issues_hash.get(statics.id_list[statics.row_selected])
                people_items.append(selected_row.get("person_responsible"))
                issue_sources_items.append(selected_row.get("source"))
                locations_items.append(selected_row.get("location"))
                end_date = selected_row.get("end_date")
                update_end_date = QDate.fromString(end_date, 'yyyy-MM-dd')
                priority_items.append(selected_row.get("priority"))
                #TODO change dropdown adding items wrongly
            else:
                print("sum ting wong")
                print('self.close()')
                #TODO give error feedback of course


        # Widgets
        self.person_responsible_label = QLabel("Person Responsible:")
        self.person_responsible_dropdown = QComboBox()
        self.populate_dropdown(self.person_responsible_dropdown, people_items, is_new_issue)



        self.originator_label = QLabel("Originator:")
        self.originator_dropdown = QComboBox()
        self.populate_dropdown(self.originator_dropdown,
                               "")  # TODO: Remove originator and link to profile signed in
        # TODO or maybe just leave it in and grey it out

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, ["Class A - LTI", "Class B - MTC", "Class C - FAC"], is_new_issue)

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, priority_items, is_new_issue)

        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, issue_sources_items, is_new_issue)

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
        if not is_new_issue:
            self.end_date_picker.setMinimumDate(update_end_date)
            self.end_date_picker.setSelectedDate(update_end_date)




        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, locations_items, is_new_issue)

        self.rectification_label = QLabel("Rectification:")
        self.rectification_entry = QTextEdit()

        self.comment_label = QLabel("Comment:")
        self.comment_entry = QTextEdit()

        save_button = custom_q_pushbutton.generate_button("Save")

        cancel_button = custom_q_pushbutton.generate_button("Cancel")

        # Layout
        v_layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Combine duration days and duration hours in a single row
        duration_row_layout = QHBoxLayout()
        duration_row_layout.addWidget(self.duration_days_text)
        duration_row_layout.addWidget(self.duration_hours_label)
        duration_row_layout.addWidget(self.duration_hours_text)

        form_layout.addRow(self.person_responsible_label, self.person_responsible_dropdown)
        form_layout.addRow(self.location_label, self.location_dropdown)
        if is_new_issue:
            form_layout.addRow(self.originator_label, self.originator_dropdown)

            form_layout.addRow(self.hazard_label, self.hazard_entry)
            form_layout.addRow(self.hazard_classification_label, self.hazard_classification_dropdown)
        form_layout.addRow(self.priority_label, self.priority_dropdown)
        if is_new_issue:
            form_layout.addRow(self.source_label, self.source_dropdown)
            form_layout.addRow(self.start_date_label, self.start_date_picker)
            form_layout.addRow(self.duration_days_label, duration_row_layout)

        form_layout.addRow(self.end_date_label, self.end_date_picker)
        if is_new_issue:
            form_layout.addRow(self.rectification_label, self.rectification_entry)

        if not is_new_issue:
            save_button.setText("Update")
            form_layout.addRow(self.comment_label, self.comment_entry)
            self.setWindowTitle("Update Issue")

        v_layout.addLayout(form_layout)
        v_layout.addWidget(save_button)
        v_layout.addWidget(cancel_button)
        self.setLayout(v_layout)

        # Connect signals
        if is_new_issue:
            self.start_date_picker.clicked.connect(lambda: self.update_end_date("from_start"))
            self.end_date_picker.clicked.connect(lambda: self.update_duration("from_end"))
            self.duration_days_text.textEdited.connect(lambda: self.update_end_date("from_duration_days"))
            self.duration_hours_text.textEdited.connect(lambda: self.update_end_date("from_duration_hours"))
            self.priority_dropdown.currentIndexChanged.connect(self.handle_priority_change)
            save_button.clicked.connect(lambda: self.save_issue)
        else:
            save_button.clicked.connect(lambda: self.update_issue)

        cancel_button.clicked.connect(self.close)

        # this ensures that no other window can receive/process input when this window is alive
        self.setWindowModality(Qt.ApplicationModal)

    def populate_dropdown(self, dropdown, items, add_blank=True):
        if add_blank:
            dropdown.addItem("")
        if len(items) > 0:
            dropdown.addItems(items)
        else:
            self.close()

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

    def update_issue(self):
        data_dict = dict(
            comment=self.comment_entry.toPlainText()
        )
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
