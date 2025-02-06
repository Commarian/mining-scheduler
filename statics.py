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
    'Due Date',      
    'Originator',
    'Start Date',
    'Hazard',
    'Source',
    'Hazard Classification',
    'Rectification',
    'Location',
    'Priority', 
    'Assignee',
    'Progress', 
    'Date Completed', 
    'Overdue',
    'Status'
]

field_mapping = {
    'Due Date': 'due_date',
    'Originator': 'originator',
    'Start Date': 'start_date',
    'Hazard': 'hazard',
    'Source': 'source',
    'Hazard Classification': 'hazard_classification',
    'Rectification': 'rectification',
    'Location': 'location',
    'Priority': 'priority',
    'Assignee': 'assignee',
    'Progress': 'progress',
    'Date Completed': 'date_completed',
    'Overdue': 'Overdue',
    'Status': 'Status'
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