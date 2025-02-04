# firebase_manager.py

import os
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore

import statics

class FirebaseManager:
    def __init__(self):
        # Initialize the Firebase app with your service account
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "docs/firebaseadminsdk.json")

        cred = credentials.Certificate(json_path)
        # Initialize a named app to avoid conflicts if multiple apps are used
        firebase_admin.initialize_app(
            cred, 
            {'databaseURL': 'https://job-card.firebaseio.com'},
            name='issues_app'
        )

        app = firebase_admin.get_app(name='issues_app')
        statics.firestoredb = firestore.client(app=app)

    # --------------------------------------------------
    #   Public Methods (Called from MainWindow, etc.)
    # --------------------------------------------------


    def set_issues(self):
        """
        Fetch job card data from Firestore 'issues' collection.
        Populate statics.issues_hash and statics.id_list.
        """
        try:
            # Clear existing data
            statics.issues_hash.clear()
            statics.id_list.clear()

            issues_coll = statics.firestoredb.collection(u'issues').get()

            # Populate statics
            for i, doc_snapshot in enumerate(issues_coll):
                doc_id = doc_snapshot.id
                doc_data = doc_snapshot.to_dict()
                statics.issues_hash.__setitem__(doc_id, doc_data)
                statics.id_list.insert(i, doc_id)

            print("Fetched issues from Firestore. statics.issues_hash updated.")
        except Exception as e:
            self.set_issues();
            print(f"Error fetching issues from Firestore: {e}, retrying...")

    def save_data(self, collection_name, data, document=None):
        """
        Save data to Firestore. Then fetch new data -> local cache -> memory.
        """
        try:
            if document:
                statics.firestoredb.collection(collection_name).document(document).set(data, merge=True)
            else:
                statics.firestoredb.collection(collection_name).add(data)
            print(f"[FirebaseManager] Data saved to Firestore: {data}")
        except Exception as e:
            self.save_data(collection_name, data, document)
            print(f"[FirebaseManager] Error saving data to Firestore: {e}, retrying...")


    def get_data(self, collection_name: str, document_name: str) -> list:
        """
        For a document whose fields are numbered string keys (e.g. "0", "1", "2", ...),
        return the values in ascending numeric order as a Python list.
        Example doc structure:
            {
                "0": "Albert Ntshangase",
                "1": "Anton Gregory",
                "10": "Jaco Salim",
                ...
            }
        """
        try:
            doc_ref = statics.firestoredb.collection(collection_name).document(document_name)
            doc_snapshot = doc_ref.get()
            if doc_snapshot.exists:
                data_dict = doc_snapshot.to_dict()  # e.g. {"0": "Albert", "1": "Anton", "10": "Jaco", ...}
                # Convert the string keys ("0", "1", "10") to integers, sort them, then retrieve values.
                sorted_keys = sorted(data_dict.keys(), key=lambda k: int(k))
                return [data_dict[k] for k in sorted_keys]
            else:
                print(f"Document '{document_name}' does not exist in '{collection_name}'.")
                return []
        except Exception as e:
            print(f"Error fetching document from Firestore: {e}")
            return []
        
    def get_organization_by_domain(self, domain):
        """
        Query the 'organizations' collection for an org document that
        has a matching domain in its 'domains' array.
        """
        try:
            doc_ref = statics.firestoredb.collection('organizations').document(domain)
            doc_snapshot = doc_ref.get()  # Fetch the document snapshot
            if doc_snapshot.exists:
                return doc_snapshot.to_dict()
            else:
                print(f"No organization found for domain: {domain}")
                return None
        except Exception as e:
            print(f"Error fetching organization: {e}")
        return None
    
    def verify_org_password(self, entered_password, stored_hash):
        try:
            return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception as e:
            print(f"Error verifying organization password: {e}")
            return False
        