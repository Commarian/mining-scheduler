# new_issue_window.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QFormLayout, \
    QStackedWidget

from firebase_manager import FirebaseManager


class FieldSetupWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):
        self.field_name_entry = QLineEdit(self)
        self.field_type_dropdown = QComboBox(self)
        self.field_type_dropdown.addItems(["text", "dropdown", "text_area"])

        add_field_button = QPushButton("Add Field", self)
        add_field_button.clicked.connect(self.add_field)

        layout = QFormLayout(self)
        layout.addRow("Field Name:", self.field_name_entry)
        layout.addRow("Field Type:", self.field_type_dropdown)
        layout.addWidget(add_field_button)

    def add_field(self):
        field_name = self.field_name_entry.text()
        field_type = self.field_type_dropdown.currentText()

        if field_name and field_type:
            self.parent().add_configurable_field({"name": field_name, "type": field_type})
            self.field_name_entry.clear()


class NewIssueWindow(QWidget):
    def __init__(self, firebase_manager):
        super().__init__()

        self.firebase_manager = firebase_manager
        self.configurable_fields = []

        self.setup_ui()

    def setup_ui(self):
        self.field_setup_widget = FieldSetupWidget()

        self.stacked_widget = QStackedWidget(self)

        save_button = QPushButton("Save Jobcard", self)
        save_button.clicked.connect(self.save_data)

        layout = QVBoxLayout(self)
        layout.addWidget(self.field_setup_widget)
        layout.addWidget(self.stacked_widget)
        layout.addWidget(save_button)

    def add_configurable_field(self, field):
        self.configurable_fields.append(field)
        self.update_stacked_widget()

    def update_stacked_widget(self):
        self.stacked_widget.clear()

        for i, field in enumerate(self.configurable_fields):
            page = QWidget()
            layout = QVBoxLayout(page)
            label = QLabel(field["name"] + ":")
            widget = self.create_input_widget(field)
            layout.addWidget(label)
            layout.addWidget(widget)
            self.stacked_widget.addWidget(page)

        self.stacked_widget.setCurrentIndex(0)  # Show the first page initially

    def create_input_widget(self, field):
        if field["type"] == "text":
            return QLineEdit()
        elif field["type"] == "dropdown":
            dropdown = QComboBox()
            # You may need to provide options for dropdown, for now, using a placeholder list
            dropdown.addItems(["Option 1", "Option 2", "Option 3"])
            return dropdown
        elif field["type"] == "text_area":
            return QTextEdit()

    def save_data(self):
        issue_data = {}

        for i, field in enumerate(self.configurable_fields):
            widget = self.stacked_widget.widget(i).layout().itemAt(1).widget()
            if isinstance(widget, QLineEdit):
                issue_data[field["name"]] = widget.text()
            elif isinstance(widget, QComboBox):
                issue_data[field["name"]] = widget.currentText()
            elif isinstance(widget, QTextEdit):
                issue_data[field["name"]] = widget.toPlainText()

        # Save job card data using FirebaseManager
        self.firebase_manager.save_jobcard_data(issue_data)

        # Optionally, emit a signal or perform other actions
