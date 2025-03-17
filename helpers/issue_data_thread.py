# helpers/issue_data_thread.py

from PyQt5.QtCore import QThread, pyqtSignal
import time  # or remove if you don't need a delay
import statics
from new_issue_list_window import IssueWindow
class IssueDataThread(QThread):
    """
    Loads data for IssueWindow in the background.
    Could be Firestore calls or any other heavy-lifting.
    """
    data_loaded = pyqtSignal(str, list, list, list)   # emits the data needed by IssueWindow

    def __init__(self, passed_in_priority, parent=None):
        super().__init__(parent)
        self.passed_in_priority = passed_in_priority

    def run(self):
        locations_items = statics.firebase_manager.get_data("company_data", "locations")
        issue_sources_items = statics.firebase_manager.get_data("company_data", "issue_sources")
        assignee_items = statics.firebase_manager.get_data("company_data", "people")
        # Now emit that data to the main thread
        self.data_loaded.emit(self.passed_in_priority, issue_sources_items, locations_items, assignee_items)
