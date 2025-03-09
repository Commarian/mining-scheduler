from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTableView, QWidget, QVBoxLayout,
    QToolBar, QAction, QStatusBar,QMessageBox
)
import datetime
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSlot, QSettings
import statics

from helpers.my_table_view import MyTableView
from helpers.table_model import TableModel
from new_issue_list_window import IssueWindow
from helpers.progress_delegate import ProgressBarDelegate
from helpers.add_record_thread import AddRecordThread
from helpers.add_record_loading_dialog import AddRecordLoadingDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Springbok", "SpringbokApp")
        self.setWindowTitle("Issue Manager")
        self.setGeometry(50, 40, 1820, 1000)
        # ===========================
        #  Global Application Style
        # ===========================
        self.setStyleSheet(statics.app_stylesheet())

        # Initialize the main parts
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.create_central_widget()
        
        #TODO add another timer that runs a boolean check on the same method passing it as a parameter to
        #TODO to check if data is old using firestore, or alternatively just fetch every 5min from firestore and check
        # Check periodically for updates to the table
        self._old_issues_hash = dict(statics.issues_hash)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(200)  # e.g. every 500 ms
        self.poll_timer.timeout.connect(self.check_for_updates)
        self.poll_timer.start()

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

        self.dark_mode_checked = self.settings.value("dark_mode", False, type=bool)
        self.dark_mode_action = QAction("Dark mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.dark_mode_checked)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)

        file_menu.addAction(self.dark_mode_action)
        file_menu.addAction(exit_action)

    def create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        add_icon = QIcon()
        add_entry_btn = QAction(add_icon, "Add Entry", self)
        add_entry_btn.triggered.connect(self.handle_add_entry)
        self.toolbar.addAction(add_entry_btn)

        update_icon = QIcon()
        self.update_entry = QAction(update_icon, "Update Record", self)
        self.update_entry.setDisabled(True)
        self.update_entry.triggered.connect(lambda: self.show_issue_window(is_new_issue=False))
        self.toolbar.addAction(self.update_entry)

    def create_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Ready")

    def create_central_widget(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.centralLayout = QVBoxLayout(central_widget)
        # Create the table model using the data that is already in statics
        model = TableModel(self.convert_issues_to_data(), statics.table_headers)
        self.table = MyTableView(model)
        self.centralLayout.addWidget(self.table)

        # Assign the ProgressBarDelegate to your 'Progress' column
        if "Progress" in statics.table_headers:
            progress_delegate = ProgressBarDelegate(self.table)
            progress_col_index = statics.table_headers.index("Progress")
            self.table.setItemDelegateForColumn(progress_col_index, progress_delegate)

        self.table.doubleClicked.connect(self.handleDoubleClick)
        
        # Connect the selectionChanged signal to a new slot
        self.table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        central_widget.setLayout(self.centralLayout)

        refresh_action = QAction(QIcon(), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_table)
        self.toolbar.addAction(refresh_action)


    def convert_issues_to_data(self):
        data = []
        issues = statics.issues_hash
        id_list = statics.id_list
        today = datetime.date.today()

        for doc_id in id_list:
            doc_data = issues.get(doc_id, {})
            # Retrieve due date from either "due_date" or fallback to "end_date"
            due_date_str = doc_data.get("due_date", doc_data.get("end_date", ""))
            if due_date_str:
                # Save the due date string so that it appears in the table
                doc_data["due_date"] = due_date_str
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
                key = statics.field_mapping.get(header)
                row.append(doc_data.get(key, ""))
            data.append(row)
        return data


    def handleDoubleClick(self, index):
        # Here, determine if you want to open the progress dialog or the issue editor.
        row_data = self.table.model()._data[index.row()]
        headers = statics.table_headers
        status_index = headers.index("Status")
        responsible_index = headers.index("Assignee")
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
        from helpers.progress_dialog import ProgressDialog
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
            statics.firebase_manager.save_data("issues", update_fields, document=doc_id)
            # Refresh the table by reloading data
            statics.firebase_manager.checkCacheAndFetch()
            self.on_thread_finished()
        

    def show_issue_window(self, is_new_issue):
        self.new_issue_list_window = IssueWindow(is_new_issue)
        self.new_issue_list_window.show()

    def closeEvent(self, event):
        if hasattr(self, 'fetch_thread') and self.fetch_thread.isRunning():
            self.fetch_thread.quit()
            self.fetch_thread.wait()
        super().closeEvent(event)

    def on_table_selection_changed(self):
        self.table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        if self.table.selectionModel().hasSelection():
            self.update_entry.setEnabled(True)
        else:
            self.update_entry.setEnabled(False)
        
    @pyqtSlot()
    def check_for_updates(self):
        # No new fetch here if you truly do it elsewhere.
        # Just compare old vs new content:
        if statics.issues_hash != self._old_issues_hash:
            print("Data changed, refreshing table...")

            # Make a fresh copy
            self._old_issues_hash = dict(statics.issues_hash)

            # Now update the UI
            self.refresh_table()

    def refresh_table(self):
        new_model = TableModel(self.convert_issues_to_data(), statics.table_headers)
        self.table.setModel(new_model)
        self.on_table_selection_changed()

    def handle_add_entry(self):
        """
        Called when user clicks 'Add Entry'. Show loading dialog immediately,
        start AddRecordThread to fetch data, then open IssueWindow on success.
        """
        self.loading_dialog = AddRecordLoadingDialog(self)
        self.loading_dialog.show()

        self.add_record_thread = AddRecordThread()
        self.add_record_thread.success.connect(self.on_add_record_success)
        self.add_record_thread.fail.connect(self.on_add_record_fail)
        self.add_record_thread.start()

    def on_add_record_success(self, data_dict):
        """
        Runs on main thread when the background thread fetches data successfully.
        data_dict => e.g. { 'locations': [...], 'issue_sources': [...], ... }
        """
        self.loading_dialog.close()

        # Now create the IssueWindow, passing it the data it needs
        self.new_issue_list_window = IssueWindow(is_new_issue=True)
        self.new_issue_list_window.show()

    def on_add_record_fail(self, error_message):
        self.loading_dialog.close()
        QMessageBox.critical(self, "Error", f"Unable to load record data: {error_message}")

    def toggle_dark_mode(self):
        self.settings.setValue("dark_mode", not self.dark_mode_checked)
        self.dark_mode_checked = not (self.dark_mode_checked)
        self.setStyleSheet(statics.app_stylesheet())
        self.dark_mode_action.setChecked(self.dark_mode_checked)