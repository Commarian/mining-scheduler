from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QToolBar, QAction, QStatusBar, QProgressDialog
)
# main_window.py
import datetime
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt

import statics

from my_table_view import MyTableView # your custom QTableView subclass
from table_model import TableModel
from new_issue_list_window import IssueWindow
from progress_delegate import ProgressBarDelegate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 1400, 800)
        # ===========================
        #  Global Application Style
        # ===========================
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f7f7; font-family: Arial; }
            QToolBar { background-color: #ffffff; border: none; }
            QToolButton { background-color: #4caf50; color: white; font-size: 14px;
                         padding: 6px 12px; border-radius: 4px; margin: 4px; }
            QToolButton:hover { background-color: #45a049; }
            QTableView { background-color: #ffffff; gridline-color: #ccc; font-size: 13px;
                        alternate-background-color: #f2f2f2; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #ccc; }
            QStatusBar { background-color: #ffffff; }
        """)

        # Initialize the main parts
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.create_central_widget()

        self.refreshTable()


    # ---------------------------
    #   Window Close Handling
    # ---------------------------
    def closeEvent(self, event):
        """
        If the thread is still running, we politely ask it to quit and wait for it.
        This avoids 'QThread: Destroyed while thread is still running' errors.
        """
        if hasattr(self, 'fetch_thread') and self.fetch_thread.isRunning():
            self.fetch_thread.quit()
            self.fetch_thread.wait()
        super().closeEvent(event)

    # ------------------------------------------------
    #   UI: Menu, Toolbar, Status Bar, Central Widget
    # ------------------------------------------------
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        add_icon = QIcon()
        add_action = QAction(add_icon, "Add Issue", self)
        add_action.triggered.connect(lambda: self.show_issue_window(is_new_issue=True))
        toolbar.addAction(add_action)

        update_icon = QIcon()
        self.update_action = QAction(update_icon, "Update Issue", self)
        self.update_action.setDisabled(True)
        self.update_action.triggered.connect(lambda: self.show_issue_window(is_new_issue=False))
        toolbar.addAction(self.update_action)

        exit_icon = QIcon()
        exit_action = QAction(exit_icon, "Exit", self)
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

    def create_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Ready")

    def create_central_widget(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # Create the table model using the data that is already in statics
        model = TableModel(self.convert_issues_to_data(), statics.table_headers)
        self.table = MyTableView(model)
        layout.addWidget(self.table)

        # Assign the ProgressBarDelegate to your 'Progress' column
        if "Progress" in statics.table_headers:
            progress_delegate = ProgressBarDelegate(self.table)
            progress_col_index = statics.table_headers.index("Progress")
            self.table.setItemDelegateForColumn(progress_col_index, progress_delegate)

        self.table.rowSelected.connect(self.handleRowSelected)
        self.table.doubleClicked.connect(self.handleDoubleClick)

        central_widget.setLayout(layout)

    # ------------------------------------------------
    #   Data / Firebase Threading
    # ------------------------------------------------
    def fetchData(self):
        # Fetch fresh data from Firestore (no cache is used)
        self.firebase_manager.set_issues()

    def convert_issues_to_data(self):
        data = []
        issues = statics.issues_hash
        id_list = statics.id_list
        today = datetime.date.today()
        field_mapping = {
            'Due Date': 'due_date',  # or fallback to 'end_date'
            'Originator': 'originator',
            'Start Date': 'start_date',
            'Hazard': 'hazard',
            'Source': 'source',
            'Hazard Classification': 'hazard_classification',
            'Rectification': 'rectification',
            'Location': 'location',
            'Priority': 'priority',
            'Person Responsible': 'person_responsible',
            'Progress': 'progress',
            'Date Completed': 'date_completed',
            'Overdue': 'Overdue',
            'Status': 'Status'
        }

        for doc_id in id_list:
            doc_data = issues.get(doc_id, {})
            # Process due date and overdue logic (same as before)
            due_date_str = doc_data.get("due_date", doc_data.get("end_date", ""))
            if due_date_str:
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    if today > due_date:
                        doc_data["Overdue"] = "Yes"
                        if not doc_data.get("Status"):
                            doc_data["Status"] = "Open"
                    else:
                        doc_data["Overdue"] = "No"
                        if not doc_data.get("Status"):
                            doc_data["Status"] = "Open"
                except Exception as e:
                    print("Error processing due_date for document", doc_id, ":", e)
                    doc_data["Overdue"] = "No"
                    if not doc_data.get("Status"):
                        doc_data["Status"] = "Open"
            else:
                doc_data["Overdue"] = "No"
                if not doc_data.get("Status"):
                    doc_data["Status"] = "Open"

            if "progress" not in doc_data or not doc_data["progress"]:
                doc_data["progress"] = "0"
            if "date_completed" not in doc_data:
                doc_data["date_completed"] = ""

            row = []
            for header in statics.table_headers:
                key = field_mapping.get(header)
                row.append(doc_data.get(key, ""))
            data.append(row)
        return data


    def handleDoubleClick(self, index):
        # Here, determine if you want to open the progress dialog or the issue editor.
        row_data = self.table.model()._data[index.row()]
        headers = statics.table_headers
        status_index = headers.index("Status")
        responsible_index = headers.index("Person Responsible")
        status = row_data[status_index]
        responsible = row_data[responsible_index]
        if status == "Open" and responsible == statics.logged_in_user:
            self.open_progress_dialog(index, is_reopening=False)
        elif status == "Closed" and getattr(statics, "logged_in_user_role", "") == "approver":
            self.open_progress_dialog(index, is_reopening=True)
        else:
            statics.row_selected = index.row()
            self.show_issue_window(is_new_issue=False)

    def open_progress_dialog(self, index, is_reopening=False):
        # Retrieve the current progress value from the table row.
        row_data = self.table.model()._data[index.row()]
        progress_index = statics.table_headers.index("Progress")
        try:
            current_progress = int(row_data[progress_index])
        except:
            current_progress = 0
        from progress_dialog import ProgressDialog
        dlg = ProgressDialog(current_progress=current_progress, parent=self)
        if dlg.exec_():
            new_progress = dlg.get_progress()
            doc_id = statics.id_list[index.row()]
            update_fields = {"progress": str(new_progress)}
            if not is_reopening:
                if new_progress == 100:
                    # Mark the issue as closed, record the completion date.
                    import datetime
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    update_fields["Status"] = "Closed"
                    update_fields["date_completed"] = today_str
            else:
                # For re-opening, if the progress is set below 100, update status to Open and clear the date.
                if new_progress < 100:
                    update_fields["Status"] = "Open"
                    update_fields["date_completed"] = ""
            self.firebase_manager.save_data("issues", update_fields, document=doc_id)
            # Refresh the table by reloading data
            self.firebase_manager.checkCacheAndFetch()
            self.on_thread_finished()

        
    def handleRowSelected(self, selected_row):
        # If needed, you can use the selected_row data.
        selected_index = self.table.selectionModel().currentIndex()
        statics.row_selected = selected_index.row()
        self.update_action.setDisabled(False)

        print("Selected Row:", selected_row)
        self.rowSelected.emit(selected_row)

    def show_issue_window(self, is_new_issue):
        """
        Opens the IssueWindow (or whichever window you use) for adding/updating an issue.
        """
        self.new_issue_list_window = IssueWindow(self.firebase_manager, is_new_issue)
        self.new_issue_list_window.show()

    def on_thread_finished(self):
        """
        Once the fresh data has been fetched in the background,
        update the table with the newly fetched data from memory.
        """
        data = self.convert_issues_to_data()
        model = TableModel(data, statics.table_headers)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()
        self.statusBar().showMessage("Data loaded successfully from Firestore.")

    def closeEvent(self, event):
        if hasattr(self, 'fetch_thread') and self.fetch_thread.isRunning():
            self.fetch_thread.quit()
            self.fetch_thread.wait()
        super().closeEvent(event)


    def refreshTable(self):
        data = self.convert_issues_to_data()
        model = TableModel(data, statics.table_headers)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()