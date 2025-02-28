#auth_window.py
import sys
import re
import bcrypt
import win32api
import statics
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import Qt
from loading_dialog import LoadingDialog
from helpers.unified_loading_dialog import UnifiedLoadingDialog
from helpers.everything_thread import EverythingThread
from helpers.data_fetcher_thread import DataFetcherThread
from main_window import MainWindow
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings

from loading_dialog import LoadingDialog

def get_current_user():
    try:
        NAME_USER_PRINCIPAL = 8  
        user_principal = win32api.GetUserNameEx(NAME_USER_PRINCIPAL)
        print(f"User Principal: {user_principal}")
    except Exception:
        print(f"User Principal exception")
        user_principal = "Unknown"
    return user_principal

def verify_password(entered_password, stored_hash):
    """
    Compare entered password with stored bcrypt hash.
    """
    try:
        return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Springbok", "SpringbokApp")  # For "Remember Me" data
        self.init_ui()

    def init_ui(self):
        statics.collected_account = get_current_user().lower()
        self.setStyleSheet(statics.app_stylesheet)
        self.password_window()

    def password_window(self):
        """
        Build the password window with a 'Remember Me' feature.
        """
        self.attempts = 0
        self.max_attempts = 5

        self.setWindowTitle('Authentication')
        self.setFixedSize(400, 250)

        main_layout = QVBoxLayout()

        # GroupBox for better visual separation
        form_group = QGroupBox("Organization Login")
        form_layout = QFormLayout()

        # Organization Input
        self.organization_input = QLineEdit()
        self.organization_input.setPlaceholderText('Enter Organization Name')
        self.organization_input.setFixedHeight(30)

        # Attempt to load saved org and password from QSettings
        saved_org = self.settings.value("org_name", "")
        saved_password = self.settings.value("org_password", "")
        remember_me_checked = self.settings.value("remember_me", False, type=bool)

        # Fill them in if they exist
        self.organization_input.setText(saved_org)

        form_layout.addRow(QLabel("Organization:"), self.organization_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter Organization Password')
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
        self.submit_button.clicked.connect(self.handle_sign_in)
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
        Called when user presses 'Sign In'. We:
        1) Show loading dialog immediately.
        2) Launch AuthThread to do the slow checks.
        3) If auth fails, we close loading and show error.
        4) If success, close auth window and proceed.
        """
        # (Optional) read user inputs again in case of any last-second changes
        self.entered_password = self.password_input.text().strip()
        self.entered_org = self.organization_input.text().strip()

        # Show the loading dialog instantly
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

        # Create the auth thread
        self.auth_thread = AuthThread(self.entered_org, self.entered_password)
        self.auth_thread.auth_success.connect(self.handle_auth_success)
        self.auth_thread.auth_fail.connect(self.handle_auth_fail)

        # Start the thread. Meanwhile, the loading dialog can animate.
        self.auth_thread.start()
            
    def start_loading_dialog(self):
        loading_dialog = LoadingDialog(self)
        loading_dialog.show()
        self.fetcher_thread = DataFetcherThread()
        self.fetcher_thread.finished_fetching.connect(loading_dialog.complete_loading)
        self.fetcher_thread.start()

    def save_credentials(self, entered_org, entered_password):
        if self.remember_checkbox.isChecked():
            self.settings.setValue("org_name", entered_org)
            self.settings.setValue("org_password", entered_password)
            self.settings.setValue("remember_me", True)
        else:
            self.clear_saved_credentials(False)

    def create_username(self):
        #Fine vir domain stripping, maar om die actual user Naam + Van te kry moet jy win32 gebruik. 
        #TODO
        current_domains = statics.logged_in_org.get("domains", [])
        #TODO KAK CODE REMOVE
        statics.username = statics.collected_account.removesuffix("@ukwazi.com").lower()

    def handle_auth_success(self, org_data):
        """
        Runs on the main (GUI) thread after auth_thread signals success.
        """
        # Close the loading dialog
        self.loading_dialog.close()

        # Org is valid, user is authorized
        statics.logged_in_org = org_data
        self.create_username()
        self.save_credentials(self.entered_org, self.entered_password)

        # Close the AuthWindow
        self.close()

        # Now do whatever you'd normally do next 
        # e.g. show a new loading dialog for fetching data, or directly fetch data
        self.start_loading_dialog()

    def handle_auth_fail(self, error_message):
        """
        Runs on the main (GUI) thread if the AuthThread fails.
        """
        # Close the loading dialog
        self.loading_dialog.close()

        # Show an error message
        QMessageBox.critical(self, "Auth Error", error_message)

        # Stay in auth window (do not close) so user can try again

    def start_loading_dialog(self):
        """
        Potentially do your data fetching next in a separate thread, or 
        do what you had in your old code. This part is up to you.
        """
        loading_dialog = LoadingDialog(self)
        loading_dialog.show()

        self.fetcher_thread = DataFetcherThread()
        self.fetcher_thread.finished_fetching.connect(loading_dialog.complete_loading)
        self.fetcher_thread.start()

    def handle_sign_in(self):
        """
        1) Show the unified loading dialog right away.
        2) Start EverythingThread for auth + data fetch.
        3) On fail => close loading, show error, remain in AuthWindow.
        4) On success => close loading, close AuthWindow, open MainWindow.
        """
        self.entered_org = self.organization_input.text().strip()
        self.entered_password = self.password_input.text().strip()

        # Show the single loading dialog
        self.loading_dialog = UnifiedLoadingDialog(self)
        self.loading_dialog.show()

        # Create the background thread
        self.everything_thread = EverythingThread(
            self.entered_org, 
            self.entered_password
        )

        # Connect the signals:
        self.everything_thread.step_progress.connect(self.loading_dialog.handle_progress_update)
        self.everything_thread.step_message.connect(self.loading_dialog.handle_message_update)
        self.everything_thread.finished_success.connect(self.on_everything_success)
        self.everything_thread.finished_fail.connect(self.on_everything_fail)

        # Start thread
        self.everything_thread.start()

    def on_everything_success(self):
        """
        Called when EverythingThread finishes successfully.
        """
        # 1) Close the loading dialog
        self.loading_dialog.close()

        # 2) Save credentials, create username, etc.
        #    Because we already verified user, 
        #    but you can finalize or store in QSettings:
        self.save_credentials(self.entered_org, self.entered_password)
        self.create_username()

        # 3) Close the AuthWindow
        self.close()

        # 4) Show the main window
        self.main_window = MainWindow()
        self.main_window.show()

    def on_everything_fail(self, error_message):
        """
        Called if auth or data fetch fails.
        """
        self.loading_dialog.close()
        QMessageBox.critical(self, "Error", error_message)
        # Remain in AuthWindow so user can re-try or fix credentials
#combined.py
#auth_window.py
import sys
import re
import bcrypt
import win32api
import statics
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import Qt
from loading_dialog import LoadingDialog
from helpers.unified_loading_dialog import UnifiedLoadingDialog
from helpers.everything_thread import EverythingThread
from helpers.data_fetcher_thread import DataFetcherThread
from main_window import MainWindow
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings

from loading_dialog import LoadingDialog

def get_current_user():
    try:
        NAME_USER_PRINCIPAL = 8  
        user_principal = win32api.GetUserNameEx(NAME_USER_PRINCIPAL)
        print(f"User Principal: {user_principal}")
    except Exception:
        print(f"User Principal exception")
        user_principal = "Unknown"
    return user_principal

def verify_password(entered_password, stored_hash):
    """
    Compare entered password with stored bcrypt hash.
    """
    try:
        return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Springbok", "SpringbokApp")  # For "Remember Me" data
        self.init_ui()

    def init_ui(self):
        statics.collected_account = get_current_user().lower()
        self.setStyleSheet(statics.app_stylesheet)
        self.password_window()

    def password_window(self):
        """
        Build the password window with a 'Remember Me' feature.
        """
        self.attempts = 0
        self.max_attempts = 5

        self.setWindowTitle('Authentication')
        self.setFixedSize(400, 250)

        main_layout = QVBoxLayout()

        # GroupBox for better visual separation
        form_group = QGroupBox("Organization Login")
        form_layout = QFormLayout()

        # Organization Input
        self.organization_input = QLineEdit()
        self.organization_input.setPlaceholderText('Enter Organization Name')
        self.organization_input.setFixedHeight(30)

        # Attempt to load saved org and password from QSettings
        saved_org = self.settings.value("org_name", "")
        saved_password = self.settings.value("org_password", "")
        remember_me_checked = self.settings.value("remember_me", False, type=bool)

        # Fill them in if they exist
        self.organization_input.setText(saved_org)

        form_layout.addRow(QLabel("Organization:"), self.organization_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter Organization Password')
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
        self.submit_button.clicked.connect(self.handle_sign_in)
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
        Called when user presses 'Sign In'. We:
        1) Show loading dialog immediately.
        2) Launch AuthThread to do the slow checks.
        3) If auth fails, we close loading and show error.
        4) If success, close auth window and proceed.
        """
        # (Optional) read user inputs again in case of any last-second changes
        self.entered_password = self.password_input.text().strip()
        self.entered_org = self.organization_input.text().strip()

        # Show the loading dialog instantly
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

        # Create the auth thread
        self.auth_thread = AuthThread(self.entered_org, self.entered_password)
        self.auth_thread.auth_success.connect(self.handle_auth_success)
        self.auth_thread.auth_fail.connect(self.handle_auth_fail)

        # Start the thread. Meanwhile, the loading dialog can animate.
        self.auth_thread.start()
            
    def start_loading_dialog(self):
        loading_dialog = LoadingDialog(self)
        loading_dialog.show()
        self.fetcher_thread = DataFetcherThread()
        self.fetcher_thread.finished_fetching.connect(loading_dialog.complete_loading)
        self.fetcher_thread.start()

    def save_credentials(self, entered_org, entered_password):
        if self.remember_checkbox.isChecked():
            self.settings.setValue("org_name", entered_org)
            self.settings.setValue("org_password", entered_password)
            self.settings.setValue("remember_me", True)
        else:
            self.clear_saved_credentials(False)

    def create_username(self):
        #Fine vir domain stripping, maar om die actual user Naam + Van te kry moet jy win32 gebruik. 
        #TODO
        current_domains = statics.logged_in_org.get("domains", [])
        #TODO KAK CODE REMOVE
        statics.username = statics.collected_account.removesuffix("@ukwazi.com").lower()

    def handle_auth_success(self, org_data):
        """
        Runs on the main (GUI) thread after auth_thread signals success.
        """
        # Close the loading dialog
        self.loading_dialog.close()

        # Org is valid, user is authorized
        statics.logged_in_org = org_data
        self.create_username()
        self.save_credentials(self.entered_org, self.entered_password)

        # Close the AuthWindow
        self.close()

        # Now do whatever you'd normally do next 
        # e.g. show a new loading dialog for fetching data, or directly fetch data
        self.start_loading_dialog()

    def handle_auth_fail(self, error_message):
        """
        Runs on the main (GUI) thread if the AuthThread fails.
        """
        # Close the loading dialog
        self.loading_dialog.close()

        # Show an error message
        QMessageBox.critical(self, "Auth Error", error_message)

        # Stay in auth window (do not close) so user can try again

    def start_loading_dialog(self):
        """
        Potentially do your data fetching next in a separate thread, or 
        do what you had in your old code. This part is up to you.
        """
        loading_dialog = LoadingDialog(self)
        loading_dialog.show()

        self.fetcher_thread = DataFetcherThread()
        self.fetcher_thread.finished_fetching.connect(loading_dialog.complete_loading)
        self.fetcher_thread.start()

    def handle_sign_in(self):
        """
        1) Show the unified loading dialog right away.
        2) Start EverythingThread for auth + data fetch.
        3) On fail => close loading, show error, remain in AuthWindow.
        4) On success => close loading, close AuthWindow, open MainWindow.
        """
        self.entered_org = self.organization_input.text().strip()
        self.entered_password = self.password_input.text().strip()

        # Show the single loading dialog
        self.loading_dialog = UnifiedLoadingDialog(self)
        self.loading_dialog.show()

        # Create the background thread
        self.everything_thread = EverythingThread(
            self.entered_org, 
            self.entered_password
        )

        # Connect the signals:
        self.everything_thread.step_progress.connect(self.loading_dialog.handle_progress_update)
        self.everything_thread.step_message.connect(self.loading_dialog.handle_message_update)
        self.everything_thread.finished_success.connect(self.on_everything_success)
        self.everything_thread.finished_fail.connect(self.on_everything_fail)

        # Start thread
        self.everything_thread.start()

    def on_everything_success(self):
        """
        Called when EverythingThread finishes successfully.
        """
        # 1) Close the loading dialog
        self.loading_dialog.close()

        # 2) Save credentials, create username, etc.
        #    Because we already verified user, 
        #    but you can finalize or store in QSettings:
        self.save_credentials(self.entered_org, self.entered_password)
        self.create_username()

        # 3) Close the AuthWindow
        self.close()

        # 4) Show the main window
        self.main_window = MainWindow()
        self.main_window.show()

    def on_everything_fail(self, error_message):
        """
        Called if auth or data fetch fails.
        """
        self.loading_dialog.close()
        QMessageBox.critical(self, "Error", error_message)
        # Remain in AuthWindow so user can re-try or fix credentials
#firebase_manager.py
# firebase_manager.py

import os
import bcrypt
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
        Save data to Firestore. Then fetch new data
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
        self.set_issues()

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
        
    def get_organization_by_domain(self, domain):
        """
        Query the 'organizations' collection for an org document that
        has a matching domain in its 'domains' array.
        """
        try:
            doc_ref = statics.firestoredb.collection('organizations').document(domain)
            doc_snapshot = doc_ref.get()  # Fetch the document snapshot
            if doc_snapshot.exists:
                return doc_snapshot.to_dict()
            else:
                print(f"No organization found for domain: {domain}")
                return None
        except Exception as e:
            print(f"Error fetching organization: {e}")
        return None
    
    def verify_org_password(self, entered_password, stored_hash):
        try:
            return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception as e:
            print(f"Error verifying organization password: {e}")
            return False
        #loading_dialog.py
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
#main.py
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

#main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTableView, QWidget, QVBoxLayout,
    QToolBar, QAction, QStatusBar,QMessageBox
)
# main_window.py
import datetime
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSlot

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

        exit_icon = QIcon()
        exit_btn = QAction(exit_icon, "Exit", self)
        exit_btn.triggered.connect(self.close)
        self.toolbar.addAction(exit_btn)

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
        self.new_issue_list_window = IssueWindow(
            is_new_issue=True, 
            pre_fetched_data=data_dict
        )
        self.new_issue_list_window.show()

    def on_add_record_fail(self, error_message):
        self.loading_dialog.close()
        QMessageBox.critical(self, "Error", f"Unable to load record data: {error_message}")
#new_issue_list_window.py
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QRegularExpression, Qt

import helpers.custom_q_pushbutton as custom_q_pushbutton
import helpers.meth as meth
import statics

class IssueWindow(QWidget):
    def __init__(self, is_new_issue, pre_fetched_data=None):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
        if (is_new_issue):
            self.access_level = 4
        else:
            self.access_level = 0
            
        self.pre_fetched_data = pre_fetched_data or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Update Record")
        self.setGeometry(50, 50, 1000, 800)

        # Populate dropdown items
        assignee_items = []
        issue_sources_items = []
        locations_items = []
        priority_items = []
        hazard_classification_items = []
        update_end_date = QDate.currentDate()

        # Originator or adding a new record
        if self.access_level > 2:
            priority_items = ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"]
            locations_items = statics.firebase_manager.get_data("company_data", "locations")
            issue_sources_items = statics.firebase_manager.get_data("company_data", "issue_sources")
            hazard_classification_items = ["Class A - LTI", "Class B - MTC", "Class C - FAC"]

        elif len(statics.id_list) > 0 and statics.row_selected is not None:
            selected_row = statics.issues_hash.get(statics.id_list[statics.row_selected])
            self.assignee = selected_row.get("assignee")
            self.originator = selected_row.get("originator")
            self.approver = selected_row.get("approver")
                
            assignee_items.append(self.assignee)
            issue_sources_items.append(selected_row.get("source"))
            locations_items.append(selected_row.get("location"))
            end_date = selected_row.get("end_date")
            update_end_date = QDate.fromString(end_date, 'yyyy-MM-dd')
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
            assignee_items = statics.firebase_manager.get_data("company_data", "people")

        # Widgets
        self.assignee_label = QLabel("Assignee:")
        self.assignee_dropdown = QComboBox()
        self.populate_dropdown(self.assignee_dropdown, assignee_items)

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, hazard_classification_items)

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, priority_items)

        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, issue_sources_items)

        self.start_date_label = QLabel("Start Date:")
        self.start_date_picker = QCalendarWidget()
        self.start_date_picker.setMinimumDate(QDate.currentDate())

        self.duration_days_label = QLabel("Duration days:")
        self.duration_days_text = QLineEdit()
        self.setup_validator(self.duration_days_text, r"^(?:[1-9][0-9]?|[1-2][0-9]{2}|3[0-5][0-9]|36[0-5])$")

        self.duration_hours_label = QLabel(" hours:")
        self.duration_hours_text = QLineEdit()
        self.setup_validator(self.duration_hours_text, r"^(?:[0-1]?[0-9]|2[0-3])$")

        self.end_date_label = QLabel("Due Date:")
        self.end_date_picker = QCalendarWidget()
        self.end_date_picker.setMinimumDate(QDate.currentDate())
        if not self.access_level > 2:
            self.end_date_picker.setMinimumDate(update_end_date)
            self.end_date_picker.setSelectedDate(update_end_date)
            
        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, locations_items)

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
            form_layout.addRow(self.hazard_label, self.hazard_entry)
            form_layout.addRow(self.hazard_classification_label, self.hazard_classification_dropdown)

        form_layout.addRow(self.priority_label, self.priority_dropdown)

        if self.access_level > 2:
            form_layout.addRow(self.source_label, self.source_dropdown)
            form_layout.addRow(self.start_date_label, self.start_date_picker)
            form_layout.addRow(self.duration_days_label, duration_row_layout)

        form_layout.addRow(self.end_date_label, self.end_date_picker)

        if (self.access_level < 2):
            self.end_date_picker.setDisabled(True)
        if self.access_level > 2:
            form_layout.addRow(self.rectification_label, self.rectification_entry)
        
        if (self.access_level > 0 and self.access_level != 4):
            form_layout.addRow(self.comment_label, self.comment_entry)

        if self.access_level == 4:
            save_button.setText("Create")
            self.setWindowTitle("Add Record")

        v_layout.addLayout(form_layout)
        v_layout.addWidget(save_button)
        v_layout.addWidget(cancel_button)
        self.setLayout(v_layout)

        # Connect signals
        if self.access_level > 0:
            self.start_date_picker.clicked.connect(lambda: self.update_end_date("from_start"))
            self.end_date_picker.clicked.connect(lambda: self.update_duration("from_end"))
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
        comment = self.comment_entry.toPlainText() if self.access_level != 4 else ""
        data_dict = dict(
            assignee=self.assignee_dropdown.currentText(),
            originator=statics.username,
            location=self.location_dropdown.currentText(),
            hazard_classification=self.hazard_classification_dropdown.currentText(),
            source=self.source_dropdown.currentText(),
            priority=self.priority_dropdown.currentText(),
            start_date=self.start_date_picker.selectedDate().toString("yyyy-MM-dd"),
            end_date=self.end_date_picker.selectedDate().toString("yyyy-MM-dd"),
            hazard=self.hazard_entry.toPlainText(),
            rectification=self.rectification_entry.toPlainText(),
            comment=comment)
    
        # If this is an existing issue => we have a row_selected doc_id.
        # If this is brand new => no doc_id.  
        if self.access_level < 4:  # means we are editing an existing one 
            doc_id = statics.id_list[statics.row_selected]
            statics.firebase_manager.save_data("issues", data_dict, document=doc_id)
        else:
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

#statics.py
# statics.py
import msal

row_selected = None
issues_hash = {}
id_list = []
public_client_app = None
firestoredb = None
logged_in_org = None
init_loading_done = False
#Accounts
collected_account = ''
username = ''

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
    'Logged Date', 
    'Start Date',
    'Due Date',
    'Date Completed', 
    'Assignee',
    'Originator',
    'Approver',
    'Hazard',
    'Source',
    'Hazard Classification',
    'Rectification',
    'Location',
    'Priority', 
    'Progress', 
    'Status',
    'Department',
    'Description'
]

field_mapping = {
    'Logged Date' : 'logged_date', 
    'Start Date': 'start_date',
    'Due Date': 'due_date',
    'Date Completed' : 'date_completed', 
    'Assignee': 'assignee', 
    'Originator': 'originator', 
    'Approver': 'approver', 
    'Hazard': 'hazard', 
    'Source': 'source', 
    'Hazard Classification': 'hazard_classification', 
    'Rectification': 'rectification', 
    'Location': 'location', 
    'Priority': 'priority', 
    'Progress': 'progress', 
    'Status': 'status', 
    'Department': 'department',
    'Description': 'description'
}

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

#helpers\add_record_loading_dialog.py
# add_record_loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
import statics

class AddRecordLoadingDialog(QDialog):
    """
    Simple 'Loading...' dialog for the Add Record flow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.setWindowTitle("Loading...")

        layout = QVBoxLayout(self)
        self.label = QLabel("Loading record data, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # A progress bar with no real progress metric (just indefinite)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)   # 0,0 => 'busy indicator'
        layout.addWidget(self.progress_bar)

#helpers\add_record_thread.py
# add_record_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class AddRecordThread(QThread):
    """
    Fetches data needed by IssueWindow, e.g. locations, issues sources, etc.
    """
    success = pyqtSignal(dict)        # emits a dictionary of needed data
    fail = pyqtSignal(str)            # emits an error message if something fails

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            # Example: fetch from Firestore
            locations = statics.firebase_manager.get_data("company_data","locations")
            issue_sources = statics.firebase_manager.get_data("company_data","issue_sources")
            # Possibly other data you need

            # Combine them in a single dict
            data = {
                "locations": locations,
                "issue_sources": issue_sources,
                # etc.
            }
            self.success.emit(data)

        except Exception as e:
            self.fail.emit(str(e))

#helpers\custom_q_pushbutton.py
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

#helpers\data_fetcher_thread.py
# data_fetcher_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class DataFetcherThread(QThread):
    finished_fetching = pyqtSignal()

    def run(self):
        # This is a synchronous call but runs in a separate thread
        statics.firebase_manager.set_issues()
        self.finished_fetching.emit()
#helpers\everything_thread.py
# everything_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics
import time

class EverythingThread(QThread):
    """
    Performs both authentication and data fetching in the background.
    We emit signals for progress, success, or fail, so the UI can be updated.
    """
    step_progress = pyqtSignal(int)  # emits a number 0-100
    step_message = pyqtSignal(str)   # emits a textual message (e.g. "Authenticating...")
    finished_success = pyqtSignal()  # signals that everything completed successfully
    finished_fail = pyqtSignal(str)  # signals an error message if something fails

    def __init__(self, org_name, password, parent=None):
        super().__init__(parent)
        self.org_name = org_name
        self.password = password

    def run(self):
        #--- PHASE 1: AUTHENTICATION ---
        self.step_message.emit("Authenticating with server...")
        self.step_progress.emit(10)  # some fake progress

        # 1) Get org data
        org_data = statics.firebase_manager.get_organization_by_domain(self.org_name)
        if not org_data:
            self.finished_fail.emit("Please double-check your organization's name.")
            return

        # 2) Verify password
        stored_hash = org_data.get("passwordHash", "")
        if not statics.firebase_manager.verify_org_password(self.password, stored_hash):
            self.finished_fail.emit("Incorrect password.")
            return

        # 3) Check authorized user
        authorized_users = org_data.get("authorizedUsers", [])
        if statics.collected_account.lower() not in [u.lower() for u in authorized_users]:
            self.finished_fail.emit("Your user account is not authorized for this organization.")
            return

        # If that all passes, we store the org on success, but keep going
        statics.logged_in_org = org_data
        self.step_progress.emit(40)
        
        #--- PHASE 2: FIRESTORE DATA FETCH ---
        self.step_message.emit("Fetching data from Firestore...")
        # Possibly a short sleep to show progress, else it might appear too quick
        time.sleep(0.5)

        # 4) Actually fetch your data
        #    If something can fail, wrap in try/except, then emit finished_fail
        try:
            statics.firebase_manager.set_issues()  # updates statics.issues_hash, statics.id_list
        except Exception as e:
            self.finished_fail.emit(f"Error fetching data: {e}")
            return

        # We are done with data fetching
        self.step_progress.emit(80)
        self.step_message.emit("Finishing up...")
        time.sleep(0.5)  # fake delay for progress bar

        # If we got here, everything was successful:
        self.step_progress.emit(100)
        self.finished_success.emit()

#helpers\meth.py
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
#helpers\my_table_view.py
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
        statics.row_selected = index.row()
        
#helpers\progress_delegate.py
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

#helpers\progress_dialog.py
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
#helpers\table_model.py
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

#helpers\unified_loading_dialog.py
# unified_loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

import statics

class UnifiedLoadingDialog(QDialog):
    """
    Shows a progress bar and a label for messages.
    We create and start the EverythingThread from here,
    or we let the AuthWindow do that. Up to you.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)

        # No close buttons, etc.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.setWindowTitle("Please wait...")

        layout = QVBoxLayout(self)

        self.label = QLabel("Initializing...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # optional Cancel button if you want the user to abort
        # self.cancel_button = QPushButton("Cancel", self)
        # self.cancel_button.clicked.connect(self.handle_cancel)
        # layout.addWidget(self.cancel_button)

    @pyqtSlot(int)
    def handle_progress_update(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def handle_message_update(self, message):
        self.label.setText(message)

    def handle_cancel(self):
        # if you let user cancel the thread:
        # self.everything_thread.terminate() or some other approach
        self.close()

#firebase_manager.py
# firebase_manager.py

import os
import bcrypt
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
        Save data to Firestore. Then fetch new data
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
        self.set_issues()

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
        
    def get_organization_by_domain(self, domain):
        """
        Query the 'organizations' collection for an org document that
        has a matching domain in its 'domains' array.
        """
        try:
            doc_ref = statics.firestoredb.collection('organizations').document(domain)
            doc_snapshot = doc_ref.get()  # Fetch the document snapshot
            if doc_snapshot.exists:
                return doc_snapshot.to_dict()
            else:
                print(f"No organization found for domain: {domain}")
                return None
        except Exception as e:
            print(f"Error fetching organization: {e}")
        return None
    
    def verify_org_password(self, entered_password, stored_hash):
        try:
            return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception as e:
            print(f"Error verifying organization password: {e}")
            return False
        #loading_dialog.py
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
#main.py
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

#main_window.py
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTableView, QWidget, QVBoxLayout,
    QToolBar, QAction, QStatusBar,QMessageBox
)
# main_window.py
import datetime
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSlot

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

        exit_icon = QIcon()
        exit_btn = QAction(exit_icon, "Exit", self)
        exit_btn.triggered.connect(self.close)
        self.toolbar.addAction(exit_btn)

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
        self.new_issue_list_window = IssueWindow(
            is_new_issue=True, 
            pre_fetched_data=data_dict
        )
        self.new_issue_list_window.show()

    def on_add_record_fail(self, error_message):
        self.loading_dialog.close()
        QMessageBox.critical(self, "Error", f"Unable to load record data: {error_message}")
#new_issue_list_window.py
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QCalendarWidget, QHBoxLayout, QFormLayout
from PyQt5.QtCore import QDate, QDateTime, QRegularExpression, Qt

import helpers.custom_q_pushbutton as custom_q_pushbutton
import helpers.meth as meth
import statics

class IssueWindow(QWidget):
    def __init__(self, is_new_issue, pre_fetched_data=None):
        super().__init__()
        self.days = 0
        self.remaining_hours = 0
        if (is_new_issue):
            self.access_level = 4
        else:
            self.access_level = 0
            
        self.pre_fetched_data = pre_fetched_data or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Update Record")
        self.setGeometry(50, 50, 1000, 800)

        # Populate dropdown items
        assignee_items = []
        issue_sources_items = []
        locations_items = []
        priority_items = []
        hazard_classification_items = []
        update_end_date = QDate.currentDate()

        # Originator or adding a new record
        if self.access_level > 2:
            priority_items = ["Critical", "Urgent", "High (A)", "Medium (B)", "Low (C)"]
            locations_items = statics.firebase_manager.get_data("company_data", "locations")
            issue_sources_items = statics.firebase_manager.get_data("company_data", "issue_sources")
            hazard_classification_items = ["Class A - LTI", "Class B - MTC", "Class C - FAC"]

        elif len(statics.id_list) > 0 and statics.row_selected is not None:
            selected_row = statics.issues_hash.get(statics.id_list[statics.row_selected])
            self.assignee = selected_row.get("assignee")
            self.originator = selected_row.get("originator")
            self.approver = selected_row.get("approver")
                
            assignee_items.append(self.assignee)
            issue_sources_items.append(selected_row.get("source"))
            locations_items.append(selected_row.get("location"))
            end_date = selected_row.get("end_date")
            update_end_date = QDate.fromString(end_date, 'yyyy-MM-dd')
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
            assignee_items = statics.firebase_manager.get_data("company_data", "people")

        # Widgets
        self.assignee_label = QLabel("Assignee:")
        self.assignee_dropdown = QComboBox()
        self.populate_dropdown(self.assignee_dropdown, assignee_items)

        self.hazard_label = QLabel("Hazard:")
        self.hazard_entry = QTextEdit()

        self.hazard_classification_label = QLabel("Hazard Classification:")
        self.hazard_classification_dropdown = QComboBox()
        self.populate_dropdown(self.hazard_classification_dropdown, hazard_classification_items)

        self.priority_label = QLabel("Priority:")
        self.priority_dropdown = QComboBox()
        self.populate_dropdown(self.priority_dropdown, priority_items)

        self.source_label = QLabel("Source:")
        self.source_dropdown = QComboBox()
        self.populate_dropdown(self.source_dropdown, issue_sources_items)

        self.start_date_label = QLabel("Start Date:")
        self.start_date_picker = QCalendarWidget()
        self.start_date_picker.setMinimumDate(QDate.currentDate())

        self.duration_days_label = QLabel("Duration days:")
        self.duration_days_text = QLineEdit()
        self.setup_validator(self.duration_days_text, r"^(?:[1-9][0-9]?|[1-2][0-9]{2}|3[0-5][0-9]|36[0-5])$")

        self.duration_hours_label = QLabel(" hours:")
        self.duration_hours_text = QLineEdit()
        self.setup_validator(self.duration_hours_text, r"^(?:[0-1]?[0-9]|2[0-3])$")

        self.end_date_label = QLabel("Due Date:")
        self.end_date_picker = QCalendarWidget()
        self.end_date_picker.setMinimumDate(QDate.currentDate())
        if not self.access_level > 2:
            self.end_date_picker.setMinimumDate(update_end_date)
            self.end_date_picker.setSelectedDate(update_end_date)
            
        self.location_label = QLabel("Location:")
        self.location_dropdown = QComboBox()
        self.populate_dropdown(self.location_dropdown, locations_items)

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
            form_layout.addRow(self.hazard_label, self.hazard_entry)
            form_layout.addRow(self.hazard_classification_label, self.hazard_classification_dropdown)

        form_layout.addRow(self.priority_label, self.priority_dropdown)

        if self.access_level > 2:
            form_layout.addRow(self.source_label, self.source_dropdown)
            form_layout.addRow(self.start_date_label, self.start_date_picker)
            form_layout.addRow(self.duration_days_label, duration_row_layout)

        form_layout.addRow(self.end_date_label, self.end_date_picker)

        if (self.access_level < 2):
            self.end_date_picker.setDisabled(True)
        if self.access_level > 2:
            form_layout.addRow(self.rectification_label, self.rectification_entry)
        
        if (self.access_level > 0 and self.access_level != 4):
            form_layout.addRow(self.comment_label, self.comment_entry)

        if self.access_level == 4:
            save_button.setText("Create")
            self.setWindowTitle("Add Record")

        v_layout.addLayout(form_layout)
        v_layout.addWidget(save_button)
        v_layout.addWidget(cancel_button)
        self.setLayout(v_layout)

        # Connect signals
        if self.access_level > 0:
            self.start_date_picker.clicked.connect(lambda: self.update_end_date("from_start"))
            self.end_date_picker.clicked.connect(lambda: self.update_duration("from_end"))
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
        comment = self.comment_entry.toPlainText() if self.access_level != 4 else ""
        data_dict = dict(
            assignee=self.assignee_dropdown.currentText(),
            originator=statics.username,
            location=self.location_dropdown.currentText(),
            hazard_classification=self.hazard_classification_dropdown.currentText(),
            source=self.source_dropdown.currentText(),
            priority=self.priority_dropdown.currentText(),
            start_date=self.start_date_picker.selectedDate().toString("yyyy-MM-dd"),
            end_date=self.end_date_picker.selectedDate().toString("yyyy-MM-dd"),
            hazard=self.hazard_entry.toPlainText(),
            rectification=self.rectification_entry.toPlainText(),
            comment=comment)
    
        # If this is an existing issue => we have a row_selected doc_id.
        # If this is brand new => no doc_id.  
        if self.access_level < 4:  # means we are editing an existing one 
            doc_id = statics.id_list[statics.row_selected]
            statics.firebase_manager.save_data("issues", data_dict, document=doc_id)
        else:
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

#statics.py
import msal

row_selected = None
issues_hash = {}
id_list = []
public_client_app = None
firestoredb = None
logged_in_org = None
init_loading_done = False
#Accounts
collected_account = ''
username = ''

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
    'Logged Date', 
    'Start Date',
    'Due Date',
    'Date Completed', 
    'Assignee',
    'Originator',
    'Approver',
    'Hazard',
    'Source',
    'Hazard Classification',
    'Rectification',
    'Location',
    'Priority', 
    'Progress', 
    'Status',
    'Department',
    'Description'
]

field_mapping = {
    'Logged Date' : 'logged_date', 
    'Start Date': 'start_date',
    'Due Date': 'due_date',
    'Date Completed' : 'date_completed', 
    'Assignee': 'assignee', 
    'Originator': 'originator', 
    'Approver': 'approver', 
    'Hazard': 'hazard', 
    'Source': 'source', 
    'Hazard Classification': 'hazard_classification', 
    'Rectification': 'rectification', 
    'Location': 'location', 
    'Priority': 'priority', 
    'Progress': 'progress', 
    'Status': 'status', 
    'Department': 'department',
    'Description': 'description'
}

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

#helpers\add_record_loading_dialog.py
# add_record_loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
import statics

class AddRecordLoadingDialog(QDialog):
    """
    Simple 'Loading...' dialog for the Add Record flow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.setWindowTitle("Loading...")

        layout = QVBoxLayout(self)
        self.label = QLabel("Loading record data, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # A progress bar with no real progress metric (just indefinite)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)   # 0,0 => 'busy indicator'
        layout.addWidget(self.progress_bar)

#helpers\add_record_thread.py
# add_record_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class AddRecordThread(QThread):
    """
    Fetches data needed by IssueWindow, e.g. locations, issues sources, etc.
    """
    success = pyqtSignal(dict)        # emits a dictionary of needed data
    fail = pyqtSignal(str)            # emits an error message if something fails

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            # Example: fetch from Firestore
            locations = statics.firebase_manager.get_data("company_data","locations")
            issue_sources = statics.firebase_manager.get_data("company_data","issue_sources")
            # Possibly other data you need

            # Combine them in a single dict
            data = {
                "locations": locations,
                "issue_sources": issue_sources,
                # etc.
            }
            self.success.emit(data)

        except Exception as e:
            self.fail.emit(str(e))

#helpers\custom_q_pushbutton.py
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

#helpers\data_fetcher_thread.py
# data_fetcher_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics

class DataFetcherThread(QThread):
    finished_fetching = pyqtSignal()

    def run(self):
        # This is a synchronous call but runs in a separate thread
        statics.firebase_manager.set_issues()
        self.finished_fetching.emit()
#helpers\everything_thread.py
# everything_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import statics
import time

class EverythingThread(QThread):
    """
    Performs both authentication and data fetching in the background.
    We emit signals for progress, success, or fail, so the UI can be updated.
    """
    step_progress = pyqtSignal(int)  # emits a number 0-100
    step_message = pyqtSignal(str)   # emits a textual message (e.g. "Authenticating...")
    finished_success = pyqtSignal()  # signals that everything completed successfully
    finished_fail = pyqtSignal(str)  # signals an error message if something fails

    def __init__(self, org_name, password, parent=None):
        super().__init__(parent)
        self.org_name = org_name
        self.password = password

    def run(self):
        #--- PHASE 1: AUTHENTICATION ---
        self.step_message.emit("Authenticating with server...")
        self.step_progress.emit(10)  # some fake progress

        # 1) Get org data
        org_data = statics.firebase_manager.get_organization_by_domain(self.org_name)
        if not org_data:
            self.finished_fail.emit("Please double-check your organization's name.")
            return

        # 2) Verify password
        stored_hash = org_data.get("passwordHash", "")
        if not statics.firebase_manager.verify_org_password(self.password, stored_hash):
            self.finished_fail.emit("Incorrect password.")
            return

        # 3) Check authorized user
        authorized_users = org_data.get("authorizedUsers", [])
        if statics.collected_account.lower() not in [u.lower() for u in authorized_users]:
            self.finished_fail.emit("Your user account is not authorized for this organization.")
            return

        # If that all passes, we store the org on success, but keep going
        statics.logged_in_org = org_data
        self.step_progress.emit(40)
        
        #--- PHASE 2: FIRESTORE DATA FETCH ---
        self.step_message.emit("Fetching data from Firestore...")
        # Possibly a short sleep to show progress, else it might appear too quick
        time.sleep(0.5)

        # 4) Actually fetch your data
        #    If something can fail, wrap in try/except, then emit finished_fail
        try:
            statics.firebase_manager.set_issues()  # updates statics.issues_hash, statics.id_list
        except Exception as e:
            self.finished_fail.emit(f"Error fetching data: {e}")
            return

        # We are done with data fetching
        self.step_progress.emit(80)
        self.step_message.emit("Finishing up...")
        time.sleep(0.5)  # fake delay for progress bar

        # If we got here, everything was successful:
        self.step_progress.emit(100)
        self.finished_success.emit()

#helpers\meth.py
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
#helpers\my_table_view.py
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
        statics.row_selected = index.row()
        
#helpers\progress_delegate.py
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

#helpers\progress_dialog.py
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
#helpers\table_model.py
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

#helpers\unified_loading_dialog.py
# unified_loading_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

import statics

class UnifiedLoadingDialog(QDialog):
    """
    Shows a progress bar and a label for messages.
    We create and start the EverythingThread from here,
    or we let the AuthWindow do that. Up to you.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(statics.app_stylesheet)

        # No close buttons, etc.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.setWindowTitle("Please wait...")

        layout = QVBoxLayout(self)

        self.label = QLabel("Initializing...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # optional Cancel button if you want the user to abort
        # self.cancel_button = QPushButton("Cancel", self)
        # self.cancel_button.clicked.connect(self.handle_cancel)
        # layout.addWidget(self.cancel_button)

    @pyqtSlot(int)
    def handle_progress_update(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def handle_message_update(self, message):
        self.label.setText(message)

    def handle_cancel(self):
        # if you let user cancel the thread:
        # self.everything_thread.terminate() or some other approach
        self.close()

