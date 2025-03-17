import msal
from PyQt5.QtCore import QSettings

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
firebase_manager = None

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
def app_stylesheet():
    if (QSettings("Springbok", "SpringbokApp").value("dark_mode", False, type=bool)):
        return dark_mode_stylesheet
    else: 
        return light_mode_stylesheet

# statics.py

light_mode_stylesheet = """
/* Global Styles */
QWidget {
    background-color: #f0f0f0;
    color: #202020;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* QLineEdit */
QLineEdit {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
}

/* QPushButton */
QPushButton {
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #45a049;
}
QPushButton:pressed {
    background-color: #3e8e41;
}
QPushButton:disabled {
    background-color: #b0b0b0;
    color: #707070;
}

/* Accept and Deny actions */
QPushButton.accept {
    background-color: #81c784;
}
QPushButton.accept:hover {
    background-color: #66bb6a;
}
QPushButton.deny {
    background-color: #e57373;
}
QPushButton.deny:hover {
    background-color: #ef5350;
}

/* QLabel */
QLabel {
    color: #202020;
}

/* QGroupBox */
QGroupBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background: transparent;
}

/* QCheckBox with custom indicator (ensure the icon exists in your resources) */
QCheckBox {
    spacing: 8px;
    font-size: 14px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #ccc;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    border: 2px solid #4caf50;
    background-color: #4caf50;
    image: url(:/icons/checkbox_checked_light.png);
}

/* QToolButton (toolbar buttons) */
QToolButton {
    background: transparent;
    border: none;
    padding: 6px;
    margin: 4px;
}
QToolButton:hover {
    background-color: rgba(76, 175, 80, 0.2);
    border-radius: 4px;
}

/* QMainWindow, QDialog */
QMainWindow, QDialog {
    background-color: #f0f0f0;
}

/* QToolBar */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #ccc;
}

/* QMenuBar and QMenu */
QMenuBar {
    background-color: #ffffff;
    color: #202020;
}
QMenuBar::item {
    background-color: #ffffff;
    color: #202020;
    padding: 6px 12px;
}
QMenuBar::item:selected {
    background-color: #4caf50;
    color: white;
}
QMenu {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #ccc;
}
QMenu::item {
    padding: 6px 20px;
}
QMenu::item:selected {
    background-color: #4caf50;
    color: white;
}

/* QTableView and QHeaderView */
QTableView {
    background-color: #ffffff;
    alternate-background-color: #f7f7f7;
    gridline-color: #ccc;
    color: #202020;
}
QHeaderView::section {
    background-color: #e0e0e0;
    color: #202020;
    padding: 8px;
    border: 1px solid #ccc;
}

/* QStatusBar */
QStatusBar {
    background-color: #ffffff;
    color: #202020;
    border-top: 1px solid #ccc;
}

/* QCalendarWidget */
QCalendarWidget QWidget {
    background-color: #ffffff;
    color: #202020;
}

/* QComboBox */
QComboBox {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #ccc;
}

/* QProgressBar */
QProgressBar {
    border: 1px solid #ccc;
    border-radius: 4px;
    text-align: center;
    color: #202020;
    padding: 2px;
}
QProgressBar::chunk {
    background-color: #4caf50;
}

/* QSlider (if used) */
QSlider::groove:horizontal {
    border: 1px solid #ccc;
    height: 8px;
    background: #eeeeee;
    margin: 2px 0;
}
QSlider::handle:horizontal {
    background: #4caf50;
    border: 1px solid #4caf50;
    width: 18px;
    margin: -2px 0;
    border-radius: 3px;
}
"""
dark_mode_stylesheet = """
/* Global Styles */
QWidget {
    background-color: #2b2b2b;
    color: #dcdcdc;
    font-family: 'Segoe UI', Arial, sans-serif;
}

/* QLineEdit */
QLineEdit {
    background-color: #3c3f41;
    color: #dcdcdc;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
}

/* QPushButton */
QPushButton {
    background-color: #3c3f41;
    color: #dcdcdc;
    border: 1px solid #e3dcdc;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QPushButton:pressed {
    background-color: #c4c0c0;
}
QPushButton:disabled {
    background-color: #636363;
    color: #a0a0a0;
}
/* Accept and Deny actions */
QPushButton.accept {
    background-color: #81c784;
}
QPushButton.accept:hover {
    background-color: #66bb6a;
}
QPushButton.deny {
    background-color: #e57373;
}
QPushButton.deny:hover {
    background-color: #ef5350;
}

/* QLabel */
QLabel {
    color: #dcdcdc;
}

/* QGroupBox */
QGroupBox {
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background: transparent;
    color: #dcdcdc;
}

/* QCheckBox with custom indicator (replace with your own dark icon) */
QCheckBox {
    spacing: 8px;
    font-size: 14px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #555;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    border: 2px solid #5a5a5a;
    background-color: #c4c0c0;
}

/* QToolButton (toolbar buttons) */
QToolButton {
    background: #121212;
    border: 2px solid #555;
    border-radius: 5px;
    padding: 6px;
    margin: 4px;
}
QToolButton:hover {
    background-color: rgba(90, 90, 90, 0.3);
    border-radius: 5px;
}
QToolButton:disabled {
    background-color: transparent;
}
/* QMainWindow, QDialog */
QMainWindow, QDialog {
    background-color: #2b2b2b;
}

/* QToolBar */
QToolBar {
    background-color: #3c3f41;
    border-bottom: 1px solid #555;
}

/* QMenuBar and QMenu */
QMenuBar {
    background-color: #3c3f41;
    color: #dcdcdc;
}
QMenuBar::item {
    background-color: #3c3f41;
    color: #dcdcdc;
    padding: 6px 12px;
}
QMenuBar::item:selected {
    background-color: #c4c0c0;
    color: #ffffff;
}
QMenu {
    background-color: #3c3f41;
    color: #dcdcdc;
    border: 1px solid #555;
}
QMenu::item {
    padding: 6px 20px;
}
QMenu::item:selected {
    background-color: #c4c0c0;
    color: #ffffff;
}

/* QTableView and QHeaderView */
QTableView {
    background-color: #3c3f41;
    alternate-background-color: #353535;
    gridline-color: #555;
    color: #dcdcdc;
}
QHeaderView::section {
    background-color: #4a4a4a;
    color: #dcdcdc;
    padding: 8px;
    border: 1px solid #555;
}

/* QStatusBar */
QStatusBar {
    background-color: #3c3f41;
    color: #dcdcdc;
    border-top: 1px solid #555;
}

/* QCalendarWidget */
QCalendarWidget QWidget {
    background-color: #3c3f41;
    color: #dcdcdc;
}

/* QComboBox */
QComboBox {
    background-color: #3c3f41;
    color: #dcdcdc;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #555;
}

/* QProgressBar */
QProgressBar {
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    color: #dcdcdc;
    padding: 2px;
}
QProgressBar::chunk {
    background-color: #c4c0c0;
}

/* QSlider (if used) */
QSlider::groove:horizontal {
    border: 1px solid #555;
    height: 8px;
    background: #444;
    margin: 2px 0;
}
QSlider::handle:horizontal {
    background: #c4c0c0;
    border: 1px solid #5a5a5a;
    width: 18px;
    margin: -2px 0;
    border-radius: 3px;
}
"""

