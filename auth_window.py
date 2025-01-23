
import re
import win32api
import win32com.client
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Get current user
        current_user = get_current_user()
        is_valid, reason = is_valid_account(current_user)

        # Set up the GUI
        layout = QVBoxLayout()
        label = QLabel()

        if is_valid:
            label.setText(f"Welcome, {current_user}!\nAccount type: {reason}")
        else:
            label.setText(f"Access Denied for {current_user}.\nReason: {reason}")

        label.setStyleSheet("font-size: 18px; color: red;" if not is_valid else "font-size: 18px; color: green;")
        layout.addWidget(label)

        self.setLayout(layout)
        self.setWindowTitle("Login Status")
        self.resize(400, 200)

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


def is_valid_account(username):
    """
    Check if the username belongs to a Microsoft account or a specific company domain.
    """
    # Example domains for validation
    microsoft_domains = ["@outlook.com", "@hotmail.com", "@gmail.com", "@microsoft.com"]
    company_domain = "@springbok.com"

    # Check if username is an email
    if re.match(r".+@.+\..+", username):
        # Check if it's a Microsoft or company account
        if any(username.endswith(domain) for domain in microsoft_domains):
            return True, "Microsoft Account"
        elif username.endswith(company_domain):
            return True, "Company Account"
        else:
            return False, "Unrecognized Email Domain"#TODO change all these GPT messages to sensible ones
    return False, "Not an Email"
