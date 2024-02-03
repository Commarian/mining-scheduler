# main_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem

from new_jobcard_window import NewJobcardWindow
from new_issue_list_window import NewIssueListWindow
from firebase_manager import FirebaseManager

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jobcard Application")
        self.setGeometry(100, 100, 400, 400)

        # Initialize FirebaseManager with the path to the service account key
        self.firebase_manager = FirebaseManager()


        self.new_jobcard_window = None
        self.new_issue_list_window = None

        new_jobcard_button = QPushButton("New Jobcard", self)
        new_jobcard_button.clicked.connect(self.show_new_jobcard_window)

        new_issue_list_button = QPushButton("New Issue List", self)
        new_issue_list_button.clicked.connect(self.show_new_issue_list_window)

        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(new_jobcard_button)
        layout.addWidget(new_issue_list_button)
        layout.addWidget(exit_button)

        #Dashboard
        jobcard_list_widget = QListWidget(self)
        self.populate_jobcards(jobcard_list_widget)
        layout.addWidget(jobcard_list_widget)

    def show_new_jobcard_window(self):
        #if not self.new_jobcard_window:
        self.new_jobcard_window = NewJobcardWindow(self.firebase_manager)
        self.new_jobcard_window.show()

    def show_new_issue_list_window(self):
        if not self.new_issue_list_window:
            self.new_issue_list_window = NewIssueListWindow()
        self.new_issue_list_window.show()

    def populate_jobcards(self, jobcard_list_widget):
        try:
            # Fetch job card data from Firestore
            jobcards = self.firebase_manager.get_jobcards()
            for jobcard in jobcards:
                title = jobcard.get("Title", "Unknown Title")
                section = jobcard.get("Section", "")
                supervisor = jobcard.get("Supervisor", "")
                shift = jobcard.get("Shift", "")
                # You can include more fields as needed

                # Create a formatted string for display
                display_text = f"{title} - {section}, {supervisor}, {shift}"

                # Create a QListWidgetItem with the formatted text
                item = QListWidgetItem(display_text)
                jobcard_list_widget.addItem(item)
        except Exception as e:
            print(f"Error fetching jobcards: {e}")
