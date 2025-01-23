import sys
import re
import win32api
import bcrypt
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt

from main_window import MainWindow

# ================================
# Configuration and Setup
# ================================

# Mapping of domains to company names
DOMAIN_COMPANY_MAP = {
    'SPRINGBOK': 'Springbok',
    'UKWAZI': 'Ukwazi',
    # Add more mappings as needed
}

# Stored hashed passwords for each company
# In production, store these securely (e.g., environment variables, secure database)
COMPANY_PASSWORD_HASHES = {
    'Springbok': b'$2a$12$FoGRJPWadBxw0Rek.SpyQ.WBirXrHLHZNSzTWbKzjmK0I0S7MzyJq',  # FIXME = xxx
    'Ukwazi': b'$2a$12$FoGRJPWadBxw0Rek.SpyQ.WBirXrHLHZNSzTWbKzjmK0I0S7MzyJq',    # FIXME DB needed to store these securely
}

# Valid company users
COMPANY_USERS = {
    'Springbok': ["anyUser@springbok.com", "drikus@ukwazi.com"],
    'Ukwazi': ["commarian1@gmail.com"],
    # Add more companies and their users as needed
}

# ================================
# Helper Functions
# ================================

def get_current_user():
    """Retrieve the current logged-in user's username."""
    try:
        # NameUserPrincipal should return something like user@domain for Microsoft accounts
        NAME_USER_PRINCIPAL = 8  # constant from PyWin32
        user_principal = win32api.GetUserNameEx(NAME_USER_PRINCIPAL)
        print(f"User Principal: {user_principal}")
        """This printed: User Principal: drikus@ukwazi.com"""
    except Exception as e:
        username = "Unknown"
    return "anyUser@springbok.com"

def get_company_from_domain(user_principal):
    """
    Determine the company based on the user's domain.
    Assumes user_principal is in the format user@domain.com
    """
    try:
        domain_match = re.search(r'@([\w.-]+)', user_principal)
        if domain_match:
            domain_full = domain_match.group(1).upper()
            # Extract the primary domain (e.g., 'ukwazi' from 'ukwazi.com')
            primary_domain = domain_full.split('.')[0]
            company = DOMAIN_COMPANY_MAP.get(primary_domain, 'Unknown Company')
            return company
        else:
            return 'Unknown Company'
    except Exception as e:
        print(f"Error determining company from domain: {e}")
        return 'Unknown Company'

def is_valid_account(username, company):
    """
    Check if the username exists within the company's user list.
    """
    valid_users = COMPANY_USERS.get(company, [])
    if username in valid_users:
        return True, "Authenticated successfully."
    else:
        return False, "Authentication failed."

def verify_password(entered_password, stored_hash):
    """
    Verify the entered password against the stored bcrypt hash.
    """
    try:
        return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

# ================================
# PyQt5 Authentication Windows
# ================================

class AuthWindow(QWidget):
    """
    Initial Authentication Window based on domain.
    Displays a welcome message if valid, or access denied.
    Proceeds to additional password authentication if valid.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Get current user
        current_user = get_current_user()
        company = get_company_from_domain(current_user)
        is_valid, reason = is_valid_account(current_user, company)

        if is_valid:
            self.password_window(company)

        else:
            # Set up the GUI
            layout = QVBoxLayout()
            self.label = QLabel()
            self.label.setText(f"Access Denied for {current_user}.\nReason: {reason}")
            self.label.setStyleSheet("font-size: 18px; color: red;")
            layout.addWidget(self.label)

            self.setLayout(layout)
            self.setWindowTitle("Login Failed")
            self.resize(400, 200)

    def password_window(self, company_name):
            self.password_hash = COMPANY_PASSWORD_HASHES.get(company_name)
            self.attempts = 0
            self.max_attempts = 3
            if not self.password_hash:
                QMessageBox.critical(self, 'Error', f'No password configured for {company_name}.')
                sys.exit(1)

            self.setWindowTitle('Additional Authentication')
            self.setFixedSize(400, 200)

            layout = QVBoxLayout()

            # Company Name Label
            self.organization_input = QLineEdit()
            self.organization_input.setText(company_name)
            self.organization_input.setFixedHeight(30)
            layout.addWidget(self.organization_input)

            # Password Input
            self.password_input = QLineEdit()
            self.password_input.setPlaceholderText('Enter Company Password')
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setFixedHeight(30)
            layout.addWidget(self.password_input)

            # Submit Button
            self.submit_button = QPushButton('Authenticate')
            self.submit_button.setFixedHeight(40)
            self.submit_button.clicked.connect(self.authenticate)
            layout.addWidget(self.submit_button)

            self.setLayout(layout)

    def authenticate(self):
        entered_password = self.password_input.text()
        if verify_password(entered_password, self.password_hash):
            QMessageBox.information(self, 'Success', 'Authentication Successful!')
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
                sys.exit(1) #FIXME add actual DB Calls here that update attempts from certain user on each attempt

    def open_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()
