import sys
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, 
    QTableView, QToolBar, QAction, QStatusBar, QMessageBox
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt

import statics
import my_table_view  # your custom QTableView subclass
import custom_q_pushbutton
from table_model import TableModel
from multi_thread import MultiThread
from firebase_manager import FirebaseManager
from new_issue_list_window import IssueWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 1400, 800)

        # ===========================
        #  Global Application Style
        # ===========================
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f7f7f7;
                font-family: Arial;
            }
            QToolBar {
                background-color: #ffffff;
                border: none;
            }
            QToolButton {
                background-color: #4caf50;
                color: white;
                font-size: 14px;
                padding: 6px 12px;
                border-radius: 4px;
                margin: 4px;
            }
            QToolButton:hover {
                background-color: #45a049;
            }
            QTableView {
                background-color: #ffffff;
                gridline-color: #ccc;
                font-size: 13px;
                alternate-background-color: #f2f2f2;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #ccc;
            }
            QStatusBar {
                background-color: #ffffff;
            }
        """)

        # ===========================
        #   Initialize members
        # ===========================
        self.headers = [
            'End Date', 'Originator', 'Start Date', 'Hazard', 'Source',
            'Hazard Classification', 'Rectification', 'Location', 'Priority', 
            'Person Responsible'
        ]
        self.new_issue_list_window = None

        # Optional: Windows-specific logic
        if sys.platform in ["win32", "cygwin"]:
            self.do_windows_specific_task()

        # Initialize the main parts
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.create_central_widget()

        # Prepare Firebase calls
        self.firebase_manager = FirebaseManager()

        # Start a thread to fetch + cache issues
        fetch_thread = MultiThread(self.fetch_and_cache_issues)
        fetch_thread.finished_signal.connect(self.on_thread_finished)
        fetch_thread.start()

    # ------------------------------------------------
    #   UI: Menu, Toolbar, Status Bar, Central Widget
    # ------------------------------------------------
    def create_menu_bar(self):
        """
        A typical menu bar with “File” → “Exit”. 
        You can add more menus (e.g. Edit, View, Help) as needed.
        """
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_toolbar(self):
        """
        A top toolbar with Add, Update, and Exit actions.
        Using QToolBar for a modern, icon-capable toolbar.
        """
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)  # Optional: disable moving the toolbar around
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Add Issue action
        add_icon = QIcon()  # If you have an icon, do QIcon("path/to/icon.png")
        add_action = QAction(add_icon, "Add Issue", self)
        add_action.triggered.connect(lambda: self.show_issue_window(is_new_issue=True))
        toolbar.addAction(add_action)

        # Update Issue action
        update_icon = QIcon()
        self.update_action = QAction(update_icon, "Update Issue", self)
        self.update_action.setDisabled(True)  # Disabled until row is selected
        self.update_action.triggered.connect(lambda: self.show_issue_window(is_new_issue=False))
        toolbar.addAction(self.update_action)

        # Exit action
        exit_icon = QIcon()
        exit_action = QAction(exit_icon, "Exit", self)
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

    def create_status_bar(self):
        """
        A status bar at the bottom of the main window.
        """
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Ready")

    def create_central_widget(self):
        """
        The central area of the QMainWindow. Here we place the table in a layout.
        """
        # The central widget must be a QWidget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create the table
        model = TableModel([], self.headers)
        self.table = my_table_view.MyTableView(model)
        self.table.setAlternatingRowColors(True)
        self.table.rowSelected.connect(self.handleRowSelected)
        self.table.doubleClicked.connect(self.handleDoubleClick)

        layout.addWidget(self.table)
        central_widget.setLayout(layout)

    # ------------------------------------------------
    #   Data / Firebase Threading
    # ------------------------------------------------
    def fetch_and_cache_issues(self):
        """
        This is run inside a thread to keep the UI responsive.
        """
        self.firebase_manager.checkCacheAndFetch()

    def on_thread_finished(self):
        """
        Called when fetch_and_cache_issues() completes.
        Update the table model with new data.
        """
        data = self.convert_issues_to_data()
        model = TableModel(data, self.headers)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()
        self.statusBar().showMessage("Data loaded successfully")

    def convert_issues_to_data(self):
        """
        Convert `statics.issues_hash` + `statics.id_list` to 2D array for table model.
        """
        data = []
        issues = statics.issues_hash
        id_list = statics.id_list

        for doc_id in id_list:
            # Reorder columns if needed; here we just do doc_data.values().
            doc_data = issues.get(doc_id, {})
            row = list(doc_data.values())
            data.append(row)

        return data

    # ------------------------------------------------
    #   UI Logic (Add Issue, Update Issue, etc.)
    # ------------------------------------------------
    def show_issue_window(self, is_new_issue):
        self.new_issue_list_window = IssueWindow(self.firebase_manager, is_new_issue)
        self.new_issue_list_window.show()

    def handleRowSelected(self):
        """
        Called by MyTableView when a row is selected. 
        We enable the Update action here.
        """
        selected_index = self.table.selectionModel().currentIndex()
        statics.row_selected = selected_index.row()
        self.update_action.setDisabled(False)

    def handleDoubleClick(self, index):
        """
        Open the selected issue for editing on double-click.
        """
        statics.row_selected = index.row()
        self.show_issue_window(is_new_issue=False)

    # ------------------------------------------------
    #   Windows-Specific Logic
    # ------------------------------------------------
    def do_windows_specific_task(self):
        try:
            import wmi
            c = wmi.WMI()
            for account in c.Win32_UserAccount():
                if account.SIDType == 1:  # user accounts only
                    print("Name:", account.Name)
        except Exception as e:
            print(e)

    def show_authentication_error(self):
        QMessageBox.critical(
            self,
            "Authentication Error",
            "Authentication error. Please sign in to this computer with a valid company account."
        )
        self.close()
        sys.exit()


# Example usage if you need a standalone run:
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())
