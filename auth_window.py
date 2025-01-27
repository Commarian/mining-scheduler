import sys
import re
import bcrypt
import win32api
import statics

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QApplication, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QSpacerItem, 
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QIcon

from main_window import MainWindow

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

def is_valid_account(username, company):
    """
    Check if the username is known for this company.
    """
    valid_users = COMPANY_USERS.get(company, [])
    if username in valid_users:
        statics.logged_in_user = username #FIXME need to get a real user name and surname - this is getting the email - not here
        return True, "Authenticated successfully."
    else:
        return False, "Authentication failed."

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
        self.settings = QSettings("MyCompany", "MyApp")  # For "Remember Me" data
        self.init_ui()

    def init_ui(self):
        current_user = get_current_user()
        company = get_company_from_domain(current_user)
        is_valid, reason = is_valid_account(current_user, company)

        # Optional: Set an icon if you have one
        # self.setWindowIcon(QIcon("path/to/icon.png"))

        # Apply an overall stylesheet to the entire window
        self.setStyleSheet("""
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
            QLabel {
                font-size: 14px;
                font-weight: normal;
            }
        """)

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

    def clear_saved_credentials(self):
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
                self.clear_saved_credentials()
            self.close()
            self.open_main_window()
        else:
            self.attempts += 1
            attempts_left = self.max_attempts - self.attempts
            if attempts_left > 0:
                QMessageBox.warning(self, 'Error', f'Invalid Password. Attempts left: {attempts_left}')
                self.password_input.clear()
            else:
                QMessageBox.critical(self, 'Error', 'Maximum attempts reached. Exiting application.')
                sys.exit(1)

    def open_main_window(self):
        """
        Launch the main window upon success.
        """
        self.main_window = MainWindow()
        self.main_window.show()

