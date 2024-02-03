# firebase_manager.py
import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseManager:
    def __init__(self):
        # Initialize Firebase with offline persistence
        cred = credentials.Certificate(
            "C:/Users/Commarian/Documents/job-card-d03e0-firebase-adminsdk-u9rr7-f4df14bfa9.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://job-card.firebaseio.com',
        }, name='excel_app')
        app = firebase_admin.get_app(name='excel_app')
        self.db = firestore.client(app=app)

    def save_jobcard_data(self, jobcard_data):
        try:
            # Save job card data to Firestore
            doc_ref = self.db.collection(u'jobcards').add(jobcard_data)
            print(f"Jobcard saved to Firestore with ID: {doc_ref}")
        except Exception as e:
            print(f"Error saving jobcard to Firestore: {e}")

    def get_jobcards(self):
        try:
            # Fetch job card data from Firestore
            jobcards_ref = self.db.collection(u'jobcards')
            jobcards = jobcards_ref.get()
            jobcards_data = [doc.to_dict() for doc in jobcards]
            print("Fetched Jobcards:", jobcards_data)
            return jobcards_data
        except Exception as e:
            print(f"Error fetching jobcards from Firestore: {e}")
            return []

    def get_data(self, collection_name, document_name):
        try:
            #if(document_name not nuklll I need plugins)
            # Fetch job card data from Firestore
            doc_ref = self.db.collection(collection_name).document(document_name)
            doc = doc_ref.get().to_dict().values()
            return doc
        except Exception as e:
            print(f"Error fetching collection from Firestore: {e}")
            return []
