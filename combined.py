#.\auth_window.py
import sys
import re
import bcrypt
import win32api
import statics
from helpers.data_fetcher_thread import DataFetcherThread

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QApplication, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QIcon

from loading_dialog import LoadingDialog

# ================================
# Configuration and Setup
# ================================

DOMAIN_COMPANY_MAP = {
    'SPRINGBOK': 'Springbok',
    'UKWAZI': 'Ukwazi',
    # ...
}

COMPANY_PASSWORD_HASHES = {
    'Springbok': b'$2a$12$FoGRJPWadBxw0Rek.SpyQ.WBirXrHLHZNSzTWbKzjmK0I0S7MzyJq',
    'Ukwazi':    b'$2a$12$FoGRJPWadBxw0Rek.SpyQ.WBirXrHLHZNSzTWbKzjmK0I0S7MzyJq',
    # ...
}

COMPANY_USERS = {
    'Springbok': ["anyUser@springbok.com", "drikus@ukwazi.com"],
    'Ukwazi': ["commarian1@gmail.com"],
    # ...
}

def get_current_user():
    """
    Retrieve the current logged-in user's username.
    Example: returns something like 'drikus@ukwazi.com'
    (For demonstration, returning a fixed user.)
    """
    try:
        NAME_USER_PRINCIPAL = 8  
        user_principal = win32api.GetUserNameEx(NAME_USER_PRINCIPAL)
        print(f"User Principal: {user_principal}")
    except Exception:
        user_principal = "Unknown"
    # For testing, override:
    user_principal = "anyUser@springbok.com"
    return user_principal

def get_company_from_domain(user_principal):
    """
    Determine the company from the user principal's domain.
    """
    try:
        domain_match = re.search(r'@([\w.-]+)', user_principal)
        if domain_match:
            domain_full = domain_match.group(1).upper()
            primary_domain = domain_full.split('.')[0]
            return DOMAIN_COMPANY_MAP.get(primary_domain, 'Unknown Company')
    except Exception as e:
        print(f"Error determining company from domain: {e}")
    return 'Unknown Company'

def verify_password(entered_password, stored_hash):
    """
    Compare entered password with stored bcrypt hash.
    """
    try:
        return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def is_valid_account(username, company):
    """
    Check if the username is known for this company by retrieving
    valid accounts from Firebase. For now, we'll fall back on the local
    COMPANY_USERS mapping, but later you can replace this with a call to
    statics.firebase_manager.get_data(...) or a similar method.
    """
    valid_users = COMPANY_USERS.get(company, [])
    if username in valid_users:
        statics.logged_in_user = username
        return True, "Authenticated successfully."
    else:
        return False, "Authentication failed."

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MyCompany", "MyApp")  # For "Remember Me" data
        self.init_ui()

    def init_ui(self):
        current_user = get_current_user()
        company = get_company_from_domain(current_user)
        is_valid, reason = is_valid_account(current_user, company)

        self.setStyleSheet(statics.app_stylesheet)

        if is_valid:
            # Proceed to the password window
            self.password_window(company)
        else:
            # Access Denied
            layout = QVBoxLayout()
            self.label = QLabel(f"Access Denied for {current_user}.\nReason: {reason}")
            self.label.setStyleSheet("font-size: 16px; color: red;")
            self.label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.label)
            self.setLayout(layout)
            self.setWindowTitle("Login Failed")
            self.resize(400, 200)

    def password_window(self, company_name):
        """
        Build the password window with a 'Remember Me' feature.
        """
        self.password_hash = COMPANY_PASSWORD_HASHES.get(company_name)
        self.attempts = 0
        self.max_attempts = 3
        if not self.password_hash:
            QMessageBox.critical(self, 'Error', f'No password configured for {company_name}.')
            sys.exit(1)

        self.setWindowTitle('Additional Authentication')
        self.setFixedSize(400, 250)

        main_layout = QVBoxLayout()

        # GroupBox for better visual separation
        form_group = QGroupBox("Organization Login")
        form_layout = QFormLayout()

        # Organization Input
        self.organization_input = QLineEdit()
        self.organization_input.setFixedHeight(30)

        # Attempt to load saved org and password from QSettings
        saved_org = self.settings.value("org_name", "")
        saved_password = self.settings.value("org_password", "")
        remember_me_checked = self.settings.value("remember_me", False, type=bool)

        # Fill them in if they exist
        self.organization_input.setText(saved_org if saved_org else company_name)

        form_layout.addRow(QLabel("Organization:"), self.organization_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter Company Password')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(30)

        # If user had "Remember Me" checked last time, fill the password automatically
        if remember_me_checked and saved_password:
            self.password_input.setText(saved_password)

        form_layout.addRow(QLabel("Password:"), self.password_input)

        # Remember Me checkbox
        self.remember_checkbox = QCheckBox("Remember Me")
        self.remember_checkbox.setChecked(remember_me_checked)
        form_layout.addRow(self.remember_checkbox)

        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        # Button row
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton('Sign In')
        self.submit_button.clicked.connect(self.authenticate)
        button_layout.addWidget(self.submit_button)

        # (Optional) “Clear Saved” if you want an easy way to clear local stored credentials
        self.clear_button = QPushButton('Clear Saved')
        self.clear_button.clicked.connect(self.clear_saved_credentials)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Add spacer so elements are center-aligned
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)

    def clear_saved_credentials(self, show_dialog = True):
        """
        Clears the saved org name/password from QSettings.
        """
        self.settings.remove("org_name")
        self.settings.remove("org_password")
        self.settings.remove("remember_me")

        # Clear the fields on the UI
        self.organization_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)

        if (show_dialog):
            QMessageBox.information(self, "Credentials Cleared", "Saved credentials have been cleared.")

    def authenticate(self):
        """
        Check password correctness. If valid, open main window.
        """
        entered_password = self.password_input.text()
        company_name = self.organization_input.text().strip()

        if verify_password(entered_password, self.password_hash):
            # If "Remember Me" is checked, save to QSettings
            if self.remember_checkbox.isChecked():
                self.settings.setValue("org_name", company_name)
                self.settings.setValue("org_password", entered_password)
                self.settings.setValue("remember_me", True)
            else:
                # Clear any old saved credentials
                self.clear_saved_credentials(False)
            self.close()
            self.start_loading_dialog()
        else:
            self.attempts += 1
            attempts_left = self.max_attempts - self.attempts
            if attempts_left > 0:
                QMessageBox.warning(self, 'Error', f'Invalid Password. Attempts left: {attempts_left}')
                self.password_input.clear()
            else:
                QMessageBox.critical(self, 'Error', 'Maximum attempts reached. Exiting application.')
                sys.exit(1)

    def start_loading_dialog(self):
        loading_dialog = LoadingDialog(self)
        loading_dialog.show()
        self.fetcher_thread = DataFetcherThread()
        self.fetcher_thread.finished_fetching.connect(loading_dialog.complete_loading)
        self.fetcher_thread.start()

#.\combine_files_for_prompts.py
import os

def gather_python_files(root="."):
    """
    Walk through 'root' directory and collect all .py file paths
    except this script file itself.
    """
    this_script = os.path.abspath(__file__)
    py_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".py"):
                full_path = os.path.abspath(os.path.join(dirpath, fname))
                # Skip this script itself if you don't want it included
                if full_path != this_script:
                    py_files.append(full_path)
    return py_files

def remove_consecutive_blank_lines(lines):
    """
    Given a list of lines, collapse consecutive blank lines into a single one.
    """
    new_lines = []
    previous_blank = False
    
    for line in lines:
        # Check if the line is empty or only whitespace
        if line.strip() == "":
            if not previous_blank:
                new_lines.append(line)
            previous_blank = True
        else:
            new_lines.append(line)
            previous_blank = False
    
    return new_lines

def combine_py_files(output_file="combined.py"):
    """
    Combine all .py files into a single file (default: combined.py).
    Each file is prefixed with a comment of the form:
         #/docs/<relative-path>.py
    if it's not already at the top.
    """
    py_files = gather_python_files(".")
    combined_lines = []

    for py_file in py_files:
        # Compute a relative path from current dir (.)
        relative_path = os.path.relpath(py_file, ".")
        doc_comment = f"#.\{relative_path}"

        with open(py_file, "r", encoding="utf-8") as f:
            file_lines = f.readlines()

        # Remove consecutive blank lines from the file's contents
        file_lines = remove_consecutive_blank_lines(file_lines)
        
        # Check if the file's first line is already "#/docs/<path>"
        if file_lines:
            first_line = file_lines[0].rstrip("\n")
            if first_line != doc_comment:
                combined_lines.append(doc_comment + "\n")
        else:
            # If the file is empty, we still add the doc_comment
            combined_lines.append(doc_comment + "\n")

        combined_lines.extend(file_lines)
        # Add a blank line between files so they don't mash together
        combined_lines.append("\n")

    # Finally, remove consecutive blank lines from the entire combined output
    combined_lines = remove_consecutive_blank_lines(combined_lines)

    # Write the combined output
    with open(output_file, "w", encoding="utf-8") as out:
        out.writelines(combined_lines)

if __name__ == "__main__":
    combine_py_files("combined.py")

#.\firebase_manager.py
# firebase_manager.py

import os

import firebase_admin
from firebase_admin import credentials, firestore

import statics

class FirebaseManager:
    def __init__(self):
        # Initialize the Firebase app with your service account
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "docs/firebaseadminsdk.json")

        cred = credentials.Certificate(json_path)
        # Initialize a named app to avoid conflicts if multiple apps are used
        firebase_admin.initialize_app(
            cred, 
            {'databaseURL': 'https://job-card.firebaseio.com'},
            name='issues_app'
        )

        app = firebase_admin.get_app(name='issues_app')
        statics.firestoredb = firestore.client(app=app)

    # --------------------------------------------------
    #   Public Methods (Called from MainWindow, etc.)
    # --------------------------------------------------

    def set_issues(self):
        """
        Fetch job card data from Firestore 'issues' collection.
        Populate statics.issues_hash and statics.id_list.
        """
        try:
            # Clear existing data
            statics.issues_hash.clear()
            statics.id_list.clear()

            issues_coll = statics.firestoredb.collection(u'issues').get()

            # Populate statics
            for i, doc_snapshot in enumerate(issues_coll):
                doc_id = doc_snapshot.id
                doc_data = doc_snapshot.to_dict()
                statics.issues_hash.__setitem__(doc_id, doc_data)
                statics.id_list.insert(i, doc_id)

            print("Fetched issues from Firestore. statics.issues_hash updated.")
        except Exception as e:
            self.set_issues();
            print(f"Error fetching issues from Firestore: {e}, retrying...")

    def save_data(self, collection_name, data, document=None):
        """
        Save data to Firestore. Then fetch new data -> local cache -> memory.
        """
        try:
            if document:
                statics.firestoredb.collection(collection_name).document(document).set(data, merge=True)
            else:
                statics.firestoredb.collection(collection_name).add(data)
            print(f"[FirebaseManager] Data saved to Firestore: {data}")
        except Exception as e:
            self.save_data(collection_name, data, document)
            print(f"[FirebaseManager] Error saving data to Firestore: {e}, retrying...")

    def get_data(self, collection_name: str, document_name: str) -> list:
        """
        For a document whose fields are numbered string keys (e.g. "0", "1", "2", ...),
        return the values in ascending numeric order as a Python list.
        Example doc structure:
            {
                "0": "Albert Ntshangase",
                "1": "Anton Gregory",
                "10": "Jaco Salim",
                ...
            }
        """
        try:
            doc_ref = statics.firestoredb.collection(collection_name).document(document_name)
            doc_snapshot = doc_ref.get()
            if doc_snapshot.exists:
                data_dict = doc_snapshot.to_dict()  # e.g. {"0": "Albert", "1": "Anton", "10": "Jaco", ...}
                # Convert the string keys ("0", "1", "10") to integers, sort them, then retrieve values.
                sorted_keys = sorted(data_dict.keys(), key=lambda k: int(k))
                return [data_dict[k] for k in sorted_keys]
            else:
                print(f"Document '{document_name}' does not exist in '{collection_name}'.")
                return []
        except Exception as e:
            print(f"Error fetching document from Firestore: {e}")
            return []

#.\loading_dialog.py
# loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from main_window import MainWindow
import statics

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super(LoadingDialog, self).__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)
        self.setWindowTitle("Loading Data")
        # Remove window frame for a splash-screen look
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        layout = QVBoxLayout(self)
        self.label = QLabel("Fetching data...\nPlease wait.", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Set up a progress bar that goes from 0 to 300 (milliseconds)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 300)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Timer for progress updates: update every 5ms
        self.timer = QTimer(self)
        self.timer.setInterval(5)  # 5ms interval
        self.timer.timeout.connect(self.update_progress)

        self.max_progress = 700  # progress bar maximum value (300ms)
        self.progress_value = 0
        self.attempt_count = 0
        self.max_attempts = 10

        self.timer.start()

    def update_progress(self):
        self.progress_value += 1
        if self.progress_value > self.max_progress:
            self.progress_value = self.max_progress
        self.progress_bar.setValue(self.progress_value)

        # When the progress bar is full, check if data is ready.
        if self.progress_value >= self.max_progress:
            if statics.init_loading_done:
                # Data is loaded: stop the timer and open the main window.
                self.timer.stop()
                self.open_main_window()
            else:
                # Data not ready: increment attempt count.
                self.attempt_count += 1
                if self.attempt_count < self.max_attempts:
                    # Reset the progress bar and try again.
                    self.progress_value = 0
                    self.progress_bar.setValue(self.progress_value)
                else:
                    self.timer.stop()
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Unable to load data from Firebase after several attempts."
                    )
                    self.close()

    def open_main_window(self):
        main_window = MainWindow()
        main_window.show()
        self.close()

    def complete_loading(self):
        statics.init_loading_done = True
#.\main.py
import sys

from PyQt5.QtWidgets import QApplication

from auth_window import AuthWindow
from main_window import MainWindow
from firebase_manager import FirebaseManager
import statics

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Instantiate FirebaseManager and store it for use throughout the app.
    statics.firebase_manager = FirebaseManager()
    auth_window = AuthWindow() #this is the real way of calling it
    auth_window.show() #this is the real way of calling it
    #for testing use:
    #MainWindow().show()

    sys.exit(app.exec())

#.\main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QToolBar, QAction, QStatusBar, QProgressDialog
)
# main_window.py
import datetime
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt

import statics

from helpers.my_table_view import MyTableView # your custom QTableView subclass
from helpers.table_model import TableModel
from new_issue_list_window import IssueWindow
from helpers.progress_delegate import ProgressBarDelegate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Issue Manager")
        self.setGeometry(100, 100, 1400, 800)
        # ===========================
        #  Global Application Style
        # ===========================
        self.setStyleSheet(statics.app_stylesheet)

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
        add_entry_btn = QAction(add_icon, "Add Entry", self)
        add_entry_btn.triggered.connect(lambda: self.show_issue_window(is_new_issue=True))
        toolbar.addAction(add_entry_btn)

        update_icon = QIcon()
        update_entry = QAction(update_icon, "Update Record", self)
        update_entry.setDisabled(True)
        update_entry.triggered.connect(lambda: self.show_issue_window(is_new_issue=False))
        toolbar.addAction(update_entry)

        exit_icon = QIcon()
        exit_btn = QAction(exit_icon, "Exit", self)
        exit_btn.triggered.connect(self.close)
        toolbar.addAction(exit_btn)

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

        self.table.doubleClicked.connect(self.handleDoubleClick)

        central_widget.setLayout(layout)

    # ------------------------------------------------
    #   Data / Firebase Threading
    # ------------------------------------------------
    def fetchData(self):
        # Fetch fresh data from Firestore (no cache is used)
        statics.firebase_manager.set_issues()

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
        """
        Opens the IssueWindow (or whichever window you use) for adding/updating an issue.
        """
        self.new_issue_list_window = IssueWindow(is_new_issue)
        self.new_issue_list_window.show()

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
#.\new_issue_list_window.py
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QRegularExpression, Qt

import helpers.custom_q_pushbutton as custom_q_pushbutton
import helpers.meth as meth
import statics

class IssueWindow(QWidget):
    def __init__(self, is_new_issue):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
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
            # Directly fetch the list from Firestore (already a list).
            people_items = statics.firebase_manager.get_data("company_data", "people")
            locations_items = statics.firebase_manager.get_data("company_data", "locations")
            issue_sources_items = statics.firebase_manager.get_data("company_data", "issue_sources")
        else:
            if len(statics.id_list) > 0 and statics.row_selected is not None:
                selected_row = statics.issues_hash.get(statics.id_list[statics.row_selected])
                people_items.append(selected_row.get("person_responsible"))
                issue_sources_items.append(selected_row.get("source"))
                locations_items.append(selected_row.get("location"))
                end_date = selected_row.get("end_date")
                update_end_date = QDate.fromString(end_date, 'yyyy-MM-dd')
                priority_items.append(selected_row.get("priority"))
            else:
                print("sum ting wong")
                print('self.close()')
                #TODO give error feedback of course

        # Widgets
        self.person_responsible_label = QLabel("Person Responsible:")
        self.person_responsible_dropdown = QComboBox()
        self.populate_dropdown(self.person_responsible_dropdown, people_items, is_new_issue)

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
            originator=statics.logged_in_user,
            location=self.location_dropdown.currentText(),
            hazard_classification=self.hazard_classification_dropdown.currentText(),
            source=self.source_dropdown.currentText(),
            priority=self.priority_dropdown.currentText(),
            start_date=self.start_date_picker.selectedDate().toString("yyyy-MM-dd"),
            end_date=self.end_date_picker.selectedDate().toString("yyyy-MM-dd"),
            hazard=self.hazard_entry.toPlainText(),
            rectification=self.rectification_entry.toPlainText())

        statics.firebase_manager.save_data("issues", data_dict)

    def update_issue(self):
        data_dict = dict(
            comment=self.comment_entry.toPlainText()
        )
        statics.firebase_manager.save_data("issues", data_dict)

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

#.\new_issue_window.py
# new_issue_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QFormLayout, \
    QStackedWidget

import statics

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
    def __init__(self):
        super().__init__()

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
        statics.firebase_manager.save_jobcard_data(issue_data)

        # Optionally, emit a signal or perform other actions

#.\statics.py
# statics.py
import msal

row_selected = None
issues_hash = {}
id_list = []
public_client_app = None
firestoredb = None
logged_in_user = None
init_loading_done = False

# Configuration from your secure storage
CLIENT_ID = 'ef8bb5e6-6b0a-45ef-a722-c4e391290f83'
TENANT_ID = '17384930-4ac0-4b0b-94ae-e6adfeef408e'
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

CLIENT_SECRET = '935eda0c-b184-472a-8b36-bf037d93a4ee'  # For organizational accounts

config = {
    "authority": AUTHORITY,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": ["User.Read"]  # Adjust scopes based on your requirements
}
msal_app = msal.ConfidentialClientApplication(config)

# Table headers for your issues table
table_headers = [
    'Due Date',           # renamed from "End Date"
    'Originator',
    'Start Date',
    'Hazard',
    'Source',
    'Hazard Classification',
    'Rectification',
    'Location',
    'Priority', 
    'Person Responsible',
    'Progress',           # new column – numeric 0–100 (shown as a progress bar)
    'Date Completed',     # new column – when the issue was closed
    'Overdue',
    'Status'
]

app_stylesheet = """
            QWidget {
                background-color: #f7f7f7;
                font-family: Arial;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                padding: 6px;
            }
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-size: 14px;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #636363;
            }
            QLabel {
                font-size: 14px;
                font-weight: normal;
            }
            QMainWindow { background-color: #f7f7f7; font-family: Arial; }
            QToolBar { background-color: #ffffff; border: none; }
            QToolButton { background-color: #4caf50; color: white; font-size: 14px;
                         padding: 6px 12px; border-radius: 4px; margin: 4px; }
            QToolButton:disabled { background-color: #636363; color: white; font-size: 14px;
                         padding: 6px 12px; border-radius: 4px; margin: 4px; }
            QToolButton:hover { background-color: #45a049; }
            QTableView { background-color: #ffffff; gridline-color: #ccc; font-size: 13px;
                        alternate-background-color: #f2f2f2; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #ccc; }
            QStatusBar { background-color: #ffffff; }
        """
#.\helpers\custom_q_pushbutton.py
from PyQt5.QtWidgets import QPushButton

green_button_style = """
    QPushButton { background-color: #4CAF50; color: white; border: 1px solid #4CAF50; }
        QPushButton:disabled {
            background-color: #CCCCCC;  /* Custom color for disabled state */
            color: #666666;  /* Custom text color for disabled state */
        }
    """
red_button_style = """
    QPushButton { background-color: #fc0328; color: white; border: 1px solid #4CAF50; }
        QPushButton:disabled {
            background-color: #CCCCCC;  /* Custom color for disabled state */
            color: #666666;  /* Custom text color for disabled state */
        }
    """
def generate_button(text):
    btn = QPushButton(text)
    btn.setMinimumSize(60, 28)
    btn.setMaximumSize(100, 33)
    if text.lower().__contains__("exit"):
        btn.setStyleSheet(red_button_style)
    else:
        btn.setStyleSheet(green_button_style)
    return btn

#.\helpers\data_fetcher_thread.py
# data_fetcher_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class DataFetcherThread(QThread):
    finished_fetching = pyqtSignal()

    def run(self):
        # This is a synchronous call but runs in a separate thread
        statics.firebase_manager.set_issues()
        self.finished_fetching.emit()
#.\helpers\meth.py
def convert_time(duration, from_unit, to_unit):
    """
    Convert time between seconds, hours, and days.

    Parameters:
    - duration: The time duration to convert.
    - from_unit: The unit of the input duration ('seconds', 'hours', 'days').
    - to_unit: The desired unit for the output ('seconds', 'hours', 'days').

    Returns:
    The converted time duration.
    """
    conversion_factors = {
        ('seconds', 'hours'): 1 / 3600,
        ('seconds', 'days'): 1 / (3600 * 24),
        ('hours', 'seconds'): 3600,
        ('hours', 'days'): 1 / 24,
        ('days', 'seconds'): 3600 * 24,
        ('days', 'hours'): 24,
    }

    if from_unit == to_unit:
        return int(duration)

    conversion_factor = conversion_factors.get((from_unit, to_unit))
    if conversion_factor is not None:
        return int(duration * conversion_factor)
    else:
        raise ValueError(f"Conversion from {from_unit} to {to_unit} is not supported.")
#.\helpers\my_table_view.py
from PyQt5 import QtWidgets, QtCore

import statics

class MyTableView(QtWidgets.QTableView):
    rowSelected = QtCore.pyqtSignal(list)
    def __init__(self, model):
        super(MyTableView, self).__init__()

        self.setModel(model)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.clicked.connect(self.handleRowSelection)

    def handleRowSelection(self, index):
        # Get the clicked index and select the entire row
        selection_model = self.selectionModel()
        selection_model.select(index.siblingAtColumn(0), QtCore.QItemSelectionModel.SelectionFlag.Select)
        selection_model.select(index.siblingAtColumn(1), QtCore.QItemSelectionModel.SelectionFlag.Select)

        # Perform the desired action here, e.g., print the selected row data
        statics.row_selected = [self.model().data(index.siblingAtColumn(col), QtCore.Qt.ItemDataRole.DisplayRole) for col in
                        range(self.model().columnCount(QtCore.QModelIndex()))]
        
#.\helpers\progress_delegate.py
# progress_delegate.py

from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionProgressBar, QApplication
from PyQt5.QtCore import Qt

class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the progress value
        value = index.data()
        try:
            progress = int(value)
        except:
            progress = 0

        # Create the style option for the progress bar
        progressBarOption = QStyleOptionProgressBar()
        progressBarOption.rect = option.rect  # or apply a margin if you like
        progressBarOption.minimum = 0
        progressBarOption.maximum = 100
        progressBarOption.progress = progress
        progressBarOption.text = str(progress) + "%"  # remove f-string
        progressBarOption.textVisible = True

        # If the row is selected, show selection highlight
        if option.state & QStyle.State_Selected:
            progressBarOption.state = QStyle.State_Enabled | QStyle.State_Selected
        else:
            progressBarOption.state = QStyle.State_Enabled

        # Draw the progress bar
        painter.save()
        QApplication.style().drawControl(QStyle.CE_ProgressBar, progressBarOption, painter)
        painter.restore()

    def createEditor(self, parent, option, index):
        # We disable inline editing in the table itself
        return None

#.\helpers\progress_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QSlider, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, current_progress=0, parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.setWindowTitle("Update Progress")
        self.current_progress = current_progress
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.current_progress)
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(self.current_progress)
        self.slider.valueChanged.connect(self.progress_bar.setValue)
        
        layout.addWidget(QLabel("Progress:"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.slider)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save", self)
        self.cancel_btn = QPushButton("Cancel", self)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def get_progress(self):
        return self.slider.value()
#.\helpers\table_model.py
# table_model.py
from PyQt5 import QtCore, QtGui, QtWidgets

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        # Get the cell value normally
        value = self._data[index.row()][index.column()]

        # For normal display
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return value

        # Customize the font appearance
        if role == QtCore.Qt.ItemDataRole.FontRole:
            # Get the entire row
            row_data = self._data[index.row()]
            # Make sure there are enough columns (Overdue and Status are columns 10 and 11)
            if len(row_data) >= 12:
                overdue = row_data[10]
                status = row_data[11]
                font = QtGui.QFont()
                # If overdue and still open, underline the text
                if overdue == "Yes" and status == "Open":
                    font.setUnderline(True)
                return font

        # Customize the text color
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            row_data = self._data[index.row()]
            if len(row_data) >= 12:
                overdue = row_data[10]
                status = row_data[11]
                # Red text for overdue open issues, grey for overdue but closed
                if overdue == "Yes":
                    if status == "Open":
                        return QtGui.QBrush(QtGui.QColor("red"))
                    else:
                        return QtGui.QBrush(QtGui.QColor("gray"))

        if role == QtCore.Qt.ItemDataRole.EditRole:
            return value

        return None

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        if self._data:
            return len(self._data[0])
        return 0

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._headers[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def flags(self, index):
        return (QtCore.Qt.ItemFlag.ItemIsEnabled | 
                QtCore.Qt.ItemFlag.ItemIsSelectable)

