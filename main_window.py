from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTableView, QWidget, QVBoxLayout,
    QToolBar, QAction, QStatusBar,QMessageBox, QMenu, QToolButton, QToolTip
)
import datetime
from PyQt5.QtGui import QIcon, QKeySequence, QCursor
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


        self.priority_button = QToolButton(self)
        self.priority_button.setText("New Issue")  # or "Add Item", etc.
        self.priority_button.setPopupMode(QToolButton.InstantPopup)  
        # 'InstantPopup' => menu pops up on click.

        # 2) Create a menu with multiple actions for different priorities.
        priority_menu = QMenu(self)
        
        critical_action = QAction("Critical Item", self)
        #critical_action.setToolTip("Critical item means X, Y, Z...")
        critical_action.triggered.connect(lambda: self.show_issue_window("critical"))

        urgent_action = QAction("Urgent Item - 6 hours", self)
        #urgent_action.setToolTip("Urgent items should be addressed ASAP...")
        urgent_action.triggered.connect(lambda: self.show_issue_window("urgent"))

        high_action = QAction("High Priority Item - 24 hours", self)
        #high_action.setToolTip("High priority requires prompt but not immediate action...")
        high_action.triggered.connect(lambda: self.show_issue_window("high"))

        medium_action = QAction("Medium Priority Item - 7 days", self)
        #medium_action.setToolTip("Medium priority items can be scheduled within a reasonable time frame...")
        medium_action.triggered.connect(lambda: self.show_issue_window("medium"))

        low_action = QAction("Low Priority Item - 14 days", self)
        #low_action.setToolTip("Low priority items have minimal impact if delayed...")
        low_action.triggered.connect(lambda: self.show_issue_window("low"))

        # 3) Add them all to the QMenu.
        priority_menu.addAction(critical_action)
        priority_menu.addAction(urgent_action)
        priority_menu.addAction(high_action)
        priority_menu.addAction(medium_action)
        priority_menu.addAction(low_action)

        # 4) Assign the menu to the QToolButton.
        self.priority_button.setMenu(priority_menu)

        # 5) Finally, add this toolbutton to the toolbar.
        self.toolbar.addWidget(self.priority_button)

        self.update_entry = QAction("Update Record", self)
        self.update_entry.setDisabled(True)
        self.update_entry.triggered.connect(lambda: self.show_issue_window("edit"))
        self.toolbar.addAction(self.update_entry)
        priority_menu.hovered.connect(self.show_action_tooltip)

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
            self.show_issue_window("edit")

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
        

    def show_issue_window(self, priority: str):
        """
        1. Show spinner dialog immediately.
        2. Spin up a background thread to load data for the new IssueWindow.
        3. Once data is loaded, close the spinner and show the IssueWindow.
        """
        from helpers.spinner_dialog import SpinnerDialog
        self.spinner = SpinnerDialog(self)  
        self.spinner.show()
        from helpers.issue_data_thread import IssueDataThread
        # Create the data thread
        self.issue_thread = IssueDataThread(priority, self)
        self.issue_thread.data_loaded.connect(self.on_issue_data_loaded)
        self.issue_thread.start()
        
    def on_issue_data_loaded(self, priority, issue_sources_items, locations_items, assignee_items): 
        self.spinner.close()
        self.new_issue_window = IssueWindow(priority, issue_sources_items, locations_items, assignee_items)
        self.new_issue_window.show()


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

    def toggle_dark_mode(self):
        self.settings.setValue("dark_mode", not self.dark_mode_checked)
        self.dark_mode_checked = not (self.dark_mode_checked)
        self.setStyleSheet(statics.app_stylesheet())
        self.dark_mode_action.setChecked(self.dark_mode_checked)
        
    def show_action_tooltip(self, action):
        if action and action.toolTip():
            # Show the action's toolTip at the mouse cursor position
            QToolTip.showText(QCursor.pos(), action.toolTip())
        else:
            # Hide any existing tooltip if there's no tooltip text
            QToolTip.hideText()
