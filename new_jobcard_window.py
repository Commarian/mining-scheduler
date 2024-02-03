# new_jobcard_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit

import firebase_manager
from firebase_manager import FirebaseManager

class NewJobcardWindow(QWidget):
    def __init__(self, firebase_manager):
        super().__init__()

        self.firebase_manager = firebase_manager
        self.setup_ui()

    def setup_ui(self):

        self.jobcard_title_label = QLabel("Jobcard Title:")
        self.jobcard_title_entry = QLineEdit()

        self.section_label = QLabel("Section:")
        self.section_dropdown = QComboBox()
        self.populate_dropdown(self.section_dropdown, self.firebase_manager.get_data(u'static_jobcard_data', u'section'))

        self.supervisor_label = QLabel("Supervisor:")
        self.supervisor_dropdown = QComboBox()
        self.populate_dropdown(self.supervisor_dropdown, ["Supervisor 1", "Supervisor 2", "Supervisor 3"])

        self.mine_area_label = QLabel("Mine Area:")
        self.mine_area_dropdown = QComboBox()
        self.populate_dropdown(self.mine_area_dropdown, ["Mine Area 1", "Mine Area 2", "Mine Area 3"])

        self.shift_label = QLabel("Shift:")
        self.shift_dropdown = QComboBox()
        self.populate_dropdown(self.shift_dropdown, ["Shift 1", "Shift 2", "Shift 3"])

        self.job_description_label = QLabel("Job Description:")
        self.job_description_entry = QTextEdit()

        self.resources_equipment_label = QLabel("Resources/Equipment:")
        self.resources_equipment_entry = QTextEdit()

        save_button = QPushButton("Save Jobcard", self)
        save_button.clicked.connect(self.save_jobcard)


        layout = QVBoxLayout(self)
        layout.addWidget(self.jobcard_title_label)
        layout.addWidget(self.jobcard_title_entry)
        layout.addWidget(self.section_label)
        layout.addWidget(self.section_dropdown)
        layout.addWidget(self.supervisor_label)
        layout.addWidget(self.supervisor_dropdown)
        layout.addWidget(self.mine_area_label)
        layout.addWidget(self.mine_area_dropdown)
        layout.addWidget(self.shift_label)
        layout.addWidget(self.shift_dropdown)
        layout.addWidget(self.job_description_label)
        layout.addWidget(self.job_description_entry)
        layout.addWidget(self.resources_equipment_label)
        layout.addWidget(self.resources_equipment_entry)
        layout.addWidget(save_button)

    def populate_dropdown(self, dropdown, items):
        dropdown.addItems(items)

    def save_jobcard(self):
        title = self.jobcard_title_entry.text()
        section = self.section_dropdown.currentText()
        supervisor = self.supervisor_dropdown.currentText()
        mine_area = self.mine_area_dropdown.currentText()
        shift = self.shift_dropdown.currentText()
        job_description = self.job_description_entry.toPlainText()
        resources_equipment = self.resources_equipment_entry.toPlainText()

        # Create a dictionary with job card data
        jobcard_data = {
            "Title": title,
            "Section": section,
            "Supervisor": supervisor,
            "MineArea": mine_area,
            "Shift": shift,
            "JobDescription": job_description,
            "ResourcesEquipment": resources_equipment
        }

        # Save job card data using FirebaseManager
        self.firebase_manager.save_jobcard_data(jobcard_data)

        # Optionally, emit a signal or perform other actions
