import sys
import re
import bcrypt
import win32api
import statics
from helpers.data_fetcher_thread import DataFetcherThread

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
        entered_password = self.password_input.text().strip()
        entered_org = self.organization_input.text().strip()
        # Retrieve organization data from Firebase:
        org_data = statics.firebase_manager.get_organization_by_domain(entered_org)
        if org_data is None:
            QMessageBox.critical(self, "Error", "Please double-check your orginization's name.")
            return

        # Verify the password against the stored hash.
        stored_hash = org_data.get("passwordHash", "")
        if statics.firebase_manager.verify_org_password(entered_password, stored_hash):
            authorized_users = org_data.get("authorizedUsers", [])
            if statics.collected_account.lower() not in [u.lower() for u in authorized_users]:
                QMessageBox.critical(self, "Error", "Your user account is not authorized for this organization.")
                return

            statics.logged_in_org = org_data
            self.create_username()
            self.save_credentials(entered_org, entered_password)
            self.close()
            self.start_loading_dialog()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password.")
            
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