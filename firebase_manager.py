# firebase_manager.py
import os

import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseManager:
    def __init__(self):
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "firebaseadminsdk.json")
        # Initialize Firebase with offline persistence
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://job-card.firebaseio.com',
        }, name='excel_app')
        app = firebase_admin.get_app(name='excel_app')
        self.db = firestore.client(app=app)

    def save_data(self, collection_name, data, document=None):
        try:
            # Save job card data to Firestore
            if document:
                doc_ref = self.db.collection(collection_name).document(document).set(data, True)
            else:
                doc_ref = self.db.collection(collection_name).add(data)

            print(f"Data to save to Firestore {data}")
            print(f"Data saved to Firestore with ID: {doc_ref}")
        except Exception as e:
            print(f"Error saving data to Firestore: {e}")

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
            doc_ref = self.db.collection(collection_name).document(document_name)
            doc = doc_ref.get().to_dict().values()
            print(f"Firebase Data = {doc}")
            return doc
        except Exception as e:
            print(f"Error fetching collection from Firestore: {e}")
            return []
