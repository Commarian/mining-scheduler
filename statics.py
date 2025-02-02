# statics.py
import msal

row_selected = None
issues_hash = {}
id_list = []
public_client_app = None
firestoredb = None
logged_in_user = None

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

# Instantiate FirebaseManager and store it for use throughout the app.
from firebase_manager import FirebaseManager
firebase_manager = FirebaseManager()
