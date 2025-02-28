from PyQt5.QtCore import QThread, pyqtSignal
import statics
import time

class EverythingThread(QThread):
    """
    Performs both authentication and data fetching in the background.
    We emit signals for progress, success, or fail, so the UI can be updated.
    """
    step_progress = pyqtSignal(int)  # emits a number 0-100
    step_message = pyqtSignal(str)   # emits a textual message (e.g. "Authenticating...")
    finished_success = pyqtSignal()  # signals that everything completed successfully
    finished_fail = pyqtSignal(str)  # signals an error message if something fails

    def __init__(self, org_name, password, parent=None):
        super().__init__(parent)
        self.org_name = org_name
        self.password = password

    def run(self):
        #--- PHASE 1: AUTHENTICATION ---
        self.step_message.emit("Authenticating with server...")
        self.step_progress.emit(10)  # some fake progress

        # 1) Get org data
        org_data = statics.firebase_manager.get_organization_by_domain(self.org_name)
        if not org_data:
            self.finished_fail.emit("Please double-check your organization's name.")
            return

        # 2) Verify password
        stored_hash = org_data.get("passwordHash", "")
        if not statics.firebase_manager.verify_org_password(self.password, stored_hash):
            self.finished_fail.emit("Incorrect password.")
            return

        # 3) Check authorized user
        authorized_users = org_data.get("authorizedUsers", [])
        if statics.collected_account.lower() not in [u.lower() for u in authorized_users]:
            self.finished_fail.emit("Your user account is not authorized for this organization.")
            return

        # If that all passes, we store the org on success, but keep going
        statics.logged_in_org = org_data
        self.step_progress.emit(40)
        
        #--- PHASE 2: FIRESTORE DATA FETCH ---
        self.step_message.emit("Fetching data from Firestore...")
        # Possibly a short sleep to show progress, else it might appear too quick
        time.sleep(0.5)

        # 4) Actually fetch your data
        #    If something can fail, wrap in try/except, then emit finished_fail
        try:
            statics.firebase_manager.set_issues()  # updates statics.issues_hash, statics.id_list
        except Exception as e:
            self.finished_fail.emit(f"Error fetching data: {e}")
            return

        # We are done with data fetching
        self.step_progress.emit(80)
        self.step_message.emit("Finishing up...")
        time.sleep(0.5)  # fake delay for progress bar

        # If we got here, everything was successful:
        self.step_progress.emit(100)
        self.finished_success.emit()
