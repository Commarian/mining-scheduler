# main_window.py
import pandas as pd

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem

from csv_data import Record

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


        new_issue_list_button = QPushButton("New Issue List", self)
        new_issue_list_button.clicked.connect(self.show_new_issue_list_window)

        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)

        import_csv_button = QPushButton("Import CSV", self)
        import_csv_button.clicked.connect(self.import_and_upload_csv)

        layout = QVBoxLayout(self)
        layout.addWidget(new_jobcard_button)
        layout.addWidget(new_issue_list_button)
        layout.addWidget(import_csv_button)
        layout.addWidget(exit_button)






        #Dashboard
        jobcard_list_widget = QListWidget(self)
        #self.populate_jobcards(jobcard_list_widget)
        layout.addWidget(jobcard_list_widget)


    def show_new_issue_list_window(self):
        if not self.new_issue_list_window:
            self.new_issue_list_window = NewIssueListWindow(self.firebase_manager)
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

    def import_and_upload_csv(self):
        file_path = 'C:\\Users\\Commarian\\PycharmProjects\\lotto\\csv.csv'

        df = pd.read_csv(file_path)
        records = []
        for index, row in df.iterrows():
            record_data = row.to_dict()
            record = Record(data=record_data)
            records.append(record)
        names_data = """
        Albert Ntshangase
        Anton Gregory
        Benjamin Smith
        Bongi (Nipho) Mkhwanazi
        Caroline Greyling
        Cindrella Venkile
        Daniel Mokoena
        Edley van Niekerk
        Eleanor Mnisi
        Esaiah Molete
        Jaco Salim
        Jannie Engelbreght
        Jeff Thabede
        Josua Bekker
        Jurgen Reynecke
        Kutlo 
        Kutlo Mokoto
        Maryna Smith 
        Mervin Barnard
        Michael 
        Micheal Rudolph
        Neil Bester
        Ntabeleng Paneng
        Riaan Gray
        Russel Booys
        Sylvia Ntalo
        T Kunene
        Themba Mulambo
        Thuso Pilane
        Vusi Mhlanga
        Yolanda Badenhorst
        Zane Preller
        """

        # Split the names and create a list of dictionaries
        names_list = [name.strip() for name in names_data.split('\n') if name.strip()]
        collection_name = "company_data"
        document_name = "people"

        data_list = [{str(i): name} for i, name in enumerate(names_list)]

        for data in data_list:
            self.firebase_manager.save_data(collection_name, data, document=document_name)