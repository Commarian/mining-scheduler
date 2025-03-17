from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QRegularExpression, Qt
import helpers.custom_q_pushbutton as custom_q_pushbutton
import helpers.meth as meth
from helpers.date_range_picker import DateRangePicker
import statics

class IssueWindow(QWidget):
    def __init__(self, passedInPriority: str, issue_sources_items, locations_items, assignee_items):
        super().__init__()
        self.setStyleSheet(statics.app_stylesheet())
        self.days = 0
        self.remaining_hours = 0
        self.assignee_items = assignee_items
        self.issue_sources_items = issue_sources_items
        self.locations_items = locations_items
        
        if (passedInPriority == "edit"):
            self.access_level = 0
        else:
            self.access_level = 4
        self.doc_id = None
        self.existing_data = {}
        if self.access_level == 0 and statics.row_selected is not None:
            self.doc_id = statics.id_list[statics.row_selected]
            self.existing_data = statics.issues_hash.get(self.doc_id, {})
            

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Update Item")
        self.setGeometry(50, 50, 1000, 800)

        # Populate dropdown items

        priority_items = []
        hazard_classification_items = []

        # Originator or adding a new record
        if self.access_level > 2:
            priority_items = ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"]
            #self.locations_items = statics.firebase_manager.get_data("company_data", "locations")
            #self.issue_sources_items = statics.firebase_manager.get_data("company_data", "issue_sources")
            hazard_classification_items = ["Class A - LTI", "Class B - MTC", "Class C - FAC"]

        elif len(statics.id_list) > 0 and statics.row_selected is not None:
            selected_row = statics.issues_hash.get(statics.id_list[statics.row_selected])
            self.assignee = selected_row.get("assignee")
            self.originator = selected_row.get("originator")
            self.approver = selected_row.get("approver")
                
            self.assignee_items.append(self.assignee)
            self.issue_sources_items.append(selected_row.get("source"))
            self.locations_items.append(selected_row.get("location"))
            priority_items.append(selected_row.get("priority"))
            hazard_classification_items.append(selected_row.get("hazard_classification"))
            #TODO add more logical handling for these items and their population based on access_level
            #Note that these get methods use STATICS field_mapping
            self.set_access_level()
        else:
            QMessageBox.critical(self, "Error", "Something went wrong with the current record selection. Please try again.")
            self.close()

        # LOGIC : Approver might be able to change the assignee
        if (self.access_level > 1):
            #self.assignee_items = statics.firebase_manager.get_data("company_data", "people")
            if self.access_level == 4:
                self.approver_label = QLabel("Approver:")
                self.approver_dropdown = QComboBox()
                self.populate_dropdown(self.approver_dropdown, self.assignee_items)
        
        # Widgets
        self.assignee_label = QLabel("Assignee:")
        self.assignee_dropdown = QComboBox()
        self.populate_dropdown(self.assignee_dropdown, self.assignee_items)

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, hazard_classification_items)

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, priority_items)

        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, self.issue_sources_items)

        self.date_range_label = QLabel("Select Date Range:")
        self.date_range_picker = DateRangePicker(self)
        self.date_range_picker.setMinimumDate(QDate.currentDate())
        self.date_range_picker.dateRangeSelected.connect(self.handle_date_range)
        

        self.duration_days_label = QLabel("Duration days:")
        self.duration_days_text = QLineEdit()
        self.setup_validator(self.duration_days_text, r"^(?:[1-9][0-9]?|[1-2][0-9]{2}|3[0-5][0-9]|36[0-5])$")

        self.duration_hours_label = QLabel("Hours allocated:")
        self.duration_hours_text = QLineEdit()
        self.setup_validator(self.duration_hours_text, r"^(?:[0-1]?[0-9]|2[0-3])$")
            
        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, self.locations_items)

        self.rectification_label = QLabel("Rectification:")
        self.rectification_entry = QTextEdit()

        self.comment_label = QLabel("Comment:")
        self.comment_entry = QTextEdit()

        save_button = custom_q_pushbutton.generate_button("Update")

        cancel_button = custom_q_pushbutton.generate_button("Cancel")

        # Layout
        v_layout = QVBoxLayout()

        form_layout = QFormLayout()
        # Combine duration days and duration hours in a single row
        duration_row_layout = QHBoxLayout()
        duration_row_layout.addWidget(self.duration_days_text)
        duration_row_layout.addWidget(self.duration_hours_label)
        duration_row_layout.addWidget(self.duration_hours_text)

        form_layout.addRow(self.assignee_label, self.assignee_dropdown)
        
        form_layout.addRow(self.location_label, self.location_dropdown)

        if self.access_level > 2:
            form_layout.addRow(self.hazard_classification_label, self.hazard_classification_dropdown)

        form_layout.addRow(self.priority_label, self.priority_dropdown)

        if self.access_level > 2:
            form_layout.addRow(self.source_label, self.source_dropdown)
            form_layout.addRow(self.duration_days_label, duration_row_layout)

        if self.access_level > 2:
            form_layout.addRow(self.rectification_label, self.rectification_entry)
        
        if (self.access_level > 0 and self.access_level != 4):
            form_layout.addRow(self.comment_label, self.comment_entry)

        if self.access_level == 4:
            save_button.setText("Create")
            self.setWindowTitle("Add Item")
            form_layout.addRow(self.approver_label, self.approver_dropdown)

        form_layout.addRow(self.date_range_label, self.date_range_picker)
        v_layout.addLayout(form_layout)
        v_layout.addWidget(save_button)
        v_layout.addWidget(cancel_button)
        self.setLayout(v_layout)

        # Connect signals
        if self.access_level > 0:
            self.duration_days_text.textEdited.connect(lambda: self.update_end_date("from_duration_days"))
            self.duration_hours_text.textEdited.connect(lambda: self.update_end_date("from_duration_hours"))
            self.priority_dropdown.currentIndexChanged.connect(self.handle_priority_change)
            save_button.clicked.connect(self.save_issue)

        cancel_button.clicked.connect(self.close)

        # This ensures that no other window can receive/process input when this window is alive
        self.setWindowModality(Qt.ApplicationModal)

    def populate_dropdown(self, dropdown, items):
        if self.access_level > 2:
            dropdown.addItem("")
        if len(items) > 0:
            dropdown.addItems(items)
        else:
            QMessageBox.critical(self, "Error", "This record is not valid. Please close it and create a new one.")
            self.close()
        # This means that we can safely assume it is not editable since only one exists.
        #TODO this must become a label when this is true, can't disable a combobox sadly
        if len(items) == 1:
            dropdown.setEditable(False)
        else:
            dropdown.setEditable(True)


    def setup_validator(self, line_edit, regex):
        validator = QRegularExpressionValidator(QRegularExpression(regex))
        line_edit.setValidator(validator)

    def save_issue(self):
        self.handle_date_range()
        comment = self.comment_entry.toPlainText() if self.access_level != 4 else ""
        if hasattr(self, 'selected_start_date') and hasattr(self, 'selected_end_date'):
            start_date_str = self.selected_start_date.toString("yyyy-MM-dd")
            end_date_str = self.selected_end_date.toString("yyyy-MM-dd")
        else:
            start_date_str = ""
            end_date_str = ""
            
        data_dict = dict(
            assignee=self.assignee_dropdown.currentText(),
            originator=statics.username,
            location=self.location_dropdown.currentText(),
            hazard_classification=self.hazard_classification_dropdown.currentText(),
            source=self.source_dropdown.currentText(),
            priority=self.priority_dropdown.currentText(),
            start_date=start_date_str,
            end_date=end_date_str,
            rectification=self.rectification_entry.toPlainText(),
            comment=comment)
    
        # If this is an existing issue => we have a row_selected doc_id.
        # If this is brand new => no doc_id.  
        if self.access_level < 4:  # means we are editing an existing one 
            doc_id = statics.id_list[statics.row_selected]
            statics.firebase_manager.save_data("issues", data_dict, document=doc_id)
        else:
            data_dict["approver"] = self.approver_dropdown.currentText()
            data_dict["logged_date"] = QDate.currentDate().toString("yyyy-MM-dd")
            statics.firebase_manager.save_data("issues", data_dict)
        self.close()

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

    def set_access_level(self):
        """ 0 = default                         - only viewing
            1 = assignee is editing             - only comments and such
            2 = approver is editing             - close record or extend deadline
            3 = originator is editing           - full access for now
            4 = creating a new issue            - full access of course
        """
        if (self.assignee is not None and self.assignee == statics.username):
            self.access_level = 1
        if (self.approver is not None and self.approver == statics.username):
            self.access_level = 2
        if (self.originator is not None and self.originator == statics.username):
            self.access_level = 3

        print("\nSetting access level to level {}\n".format(self.access_level))



    def handle_date_range(self, start_date=None, end_date=None):
        self.selected_start_date = start_date
        self.selected_end_date = end_date

        if not start_date:
            self.selected_start_date = QDate.currentDate()
        if not end_date:
            self.selected_end_date = QDate.currentDate()
            
        if self.selected_start_date and not self.selected_end_date:
            self.selected_end_date = self.selected_start_date
        if not self.selected_start_date:
            self.selected_start_date = QDate.currentDate()
        if not self.selected_end_date:
            self.selected_end_date = QDate.currentDate()
