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
