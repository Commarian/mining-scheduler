import os
import re
import subprocess
import win32com.client
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


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


# if __name__ == "__main__":
#     app = QApplication([])
#     window = LoginStatusApp()
#     window.show()
#     app.exec()
def get_microsoft_account():
    try:
        obj = win32com.client.Dispatch("WScript.Network")
        user = obj.UserName  # Fetches the logged-in user
        return user  # Returns domain\username or email
    except Exception as e:
        return str(e)
def get_current_user():
    """Retrieve the current logged-in user's username."""
    try:
        # Attempt to fetch the username





        print(f"Logged-in Microsoft account: {get_microsoft_account()}")

    except Exception as e:
        username = "Unknown"
    return username


def is_valid_account(username):
    """
    Check if the username belongs to a Microsoft account or a specific company domain.
    """
    # Example domains for validation
    microsoft_domains = ["@outlook.com", "@hotmail.com", "@gmail.com", "@microsoft.com"]
    company_domain = "@examplecompany.com"  # Replace with your company domain

    # Check if username is an email
    if re.match(r".+@.+\..+", username):
        # Check if it's a Microsoft or company account
        if any(username.endswith(domain) for domain in microsoft_domains):
            return True, "Microsoft Account"
        elif username.endswith(company_domain):
            return True, "Company Account"
        else:
            return False, "Unrecognized Email Domain"
    return False, "Not an Email"