# excel_like_app_gui.py
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QLineEdit, QLabel, \
    QComboBox, QTextEdit
import firebase_admin
from firebase_admin import credentials, firestore

class ExcelLikeAppGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Excel-Like App")

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["A", "B", "C"])

        self.data = {
            1: {"A": "", "B": "", "C": ""},
            2: {"A": "", "B": "", "C": ""},
            3: {"A": "", "B": "", "C": ""},
            4: {"A": "", "B": "", "C": ""},
            5: {"A": "", "B": "", "C": ""}
        }

        self.update_table()

        self.entry = QLineEdit(self)

        add_button = QPushButton("Add Data", self)
        add_button.clicked.connect(self.add_data)

        save_button = QPushButton("Save to Firebase", self)
        save_button.clicked.connect(self.save_to_firebase)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.entry)
        layout.addWidget(add_button)
        layout.addWidget(save_button)

        self.apply_dark_theme()



    def update_table(self):
        self.table.setRowCount(len(self.data))
        for row, values in self.data.items():
            for col, value in enumerate(values.values()):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row - 1, col, item)

    def add_data(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            value = self.entry.text()
            column = self.table.currentColumn()
            column_label = chr(ord('A') + column)
            self.data[selected_row + 1][column_label] = value  # Update local data
            self.update_table()
            self.entry.clear()

    def save_to_firebase(self):
        try:
            # Save data from QTableWidget to Firestore
            for row in range(self.table.rowCount()):
                row_data = {}
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    column_label = chr(ord('A') + col)
                    row_data[column_label] = item.text() if item else ""
                doc_ref = self.db.collection(u'excel_data').document(f'Row_{row + 1}')
                doc_ref.set(row_data)
            print("Data saved to Firebase successfully.")
        except Exception as e:
            print(f"Error saving to Firebase: {e}")

    def apply_dark_theme(self):
        # Dark theme stylesheet
        style_sheet = """
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QTableWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                gridline-color: #1E1E1E;
            }
            QTableWidget::item {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #646464;
            }
            QHeaderView::section {
                background-color: #1E1E1E;
                color: #FFFFFF;
                padding: 4px;
            }
            QLineEdit, QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #434343;
                selection-background-color: #646464;
            }
            """
        self.setStyleSheet(style_sheet)
