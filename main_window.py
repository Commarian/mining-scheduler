# main_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit
from PyQt5.QtCore import Qt

from new_issue_window import NewIssueWindow
from firebase_manager import FirebaseManager

class HyperlinkLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.linkActivated.emit(self.text())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jobcard Application")
        self.setGeometry(100, 100, 800, 600)  # Increased width for a better layout

        # Initialize FirebaseManager with the path to the service account key
        self.firebase_manager = FirebaseManager()

        self.new_jobcard_window = None
        self.new_issue_list_window = None

        # Left panel with action buttons and search
        left_panel_layout = QVBoxLayout()

        # Search bar
        search_line_edit = QLineEdit(self)
        search_line_edit.setPlaceholderText("Search...")
        left_panel_layout.addWidget(search_line_edit)

        # Action buttons styled like hyperlinks
        add_issue_label = HyperlinkLabel("Add Issue", self)
        add_issue_label.linkActivated.connect(self.show_new_issue_window)

        export_report_label = HyperlinkLabel("Export/Report", self)
        export_report_label.linkActivated.connect(self.export_report_function)

        left_panel_layout.addWidget(add_issue_label)
        left_panel_layout.addWidget(export_report_label)

        # Dashboard in the middle
        dashboard_layout = QVBoxLayout()

        # You can add widgets/components to the dashboard_layout as needed
        # For now, let's add a QListWidget to simulate the dashboard
        jobcard_list_widget = QListWidget(self)
        self.populate_jobcards(jobcard_list_widget)
        dashboard_layout.addWidget(jobcard_list_widget)

        # Main layout combining left panel and dashboard
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(left_panel_layout)
        main_layout.addLayout(dashboard_layout)

    def show_new_issue_window(self):
        self.new_issue_window = NewIssueWindow(self.firebase_manager)
        self.new_issue_window.show()

    def populate_jobcards(self, jobcard_list_widget):
        try:
            # Fetch job card data from Firestore
            jobcards = self.firebase_manager.get_jobcards()
            for jobcard in jobcards:
                title = jobcard.get("Title", "Unknown Title")
                section = jobcard.get("Section", "")
                supervisor = jobcard.get("Supervisor", "")
                shift = jobcard.get("Shift", "")

                # Create a formatted string for display
                display_text = f"{title} - {section}, {supervisor}, {shift}"

                # Create a QListWidgetItem with the formatted text
                item = QListWidgetItem(display_text)
                jobcard_list_widget.addItem(item)
        except Exception as e:
            print(f"Error fetching job cards: {e}")

    def export_report_function(self):
        # Implement export/report functionality here
        pass
