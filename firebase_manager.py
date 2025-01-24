# firebase_manager.py

import os
import json
import time

import firebase_admin
from firebase_admin import credentials, firestore, auth
from msal import PublicClientApplication

import statics

class FirebaseManager:
    def __init__(self):
        # Initialize the Firebase app with your service account
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "firebaseadminsdk.json")

        cred = credentials.Certificate(json_path)
        # Initialize a named app to avoid conflicts if multiple apps are used
        firebase_admin.initialize_app(
            cred, 
            {'databaseURL': 'https://job-card.firebaseio.com'},
            name='issues_app'
        )

        app = firebase_admin.get_app(name='issues_app')
        statics.firestoredb = firestore.client(app=app)

        # For caching
        self.local_cache_file = "cached_issues.json"  # File to store data
        self.cache_expiry_seconds = 300  # 5 minutes, for example

    # --------------------------------------------------
    #   Public Methods (Called from MainWindow, etc.)
    # --------------------------------------------------
    def checkCacheAndFetch(self):
        """
        Called to ensure we have up-to-date issues in `statics.issues_hash` and `statics.id_list`.
        If local cache is valid, loads from file; otherwise fetches from Firestore and saves cache.
        """
        if self.is_cache_valid():
            print("FirebaseManager: Local cache is valid. Loading from local cache.")
            self.load_local_cache()
        else:
            print("FirebaseManager: Cache is stale or does not exist. Fetching from Firestore.")
            self.set_issues()      # Fetch from Firestore, populate statics
            self.save_local_cache()  # Then save to local cache

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
            print(f"Error fetching issues from Firestore: {e}")

    def save_data(self, collection_name, data, document=None):
        """
        Example of how to save job card data to a specific Firestore collection.
        """
        try:
            if document:
                statics.firestoredb.collection(collection_name).document(document).set(data, merge=True)
            else:
                statics.firestoredb.collection(collection_name).add(data)

            print(f"Data saved to Firestore: {data}")
        except Exception as e:
            print(f"Error saving data to Firestore: {e}")

    def get_data(self, collection_name, document_name):
        """
        Example get method if you want a single document's data.
        """
        try:
            doc_ref = statics.firestoredb.collection(collection_name).document(document_name)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                print(f"Fetched from Firestore: {data}")
                return data
            else:
                print("Document does not exist.")
                return {}
        except Exception as e:
            print(f"Error fetching document from Firestore: {e}")
            return {}

    # --------------------------------------------------
    #   Basic Cache Logic
    # --------------------------------------------------
    def is_cache_valid(self):
        """
        Returns True if the cache file exists and is "fresh".
        In this example, we base "freshness" on file modification time 
        vs. `self.cache_expiry_seconds`.
        """
        if not os.path.exists(self.local_cache_file):
            return False

        file_mtime = os.path.getmtime(self.local_cache_file)
        now = time.time()
        if now - file_mtime < self.cache_expiry_seconds:
            return True
        return False

    def load_local_cache(self):
        """
        Load from local JSON file, populate `statics.issues_hash` and `statics.id_list`.
        """
        try:
            with open(self.local_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # Expecting a structure like:
                # {
                #    "id_list": [...],
                #    "issues": { "doc_id": {...}, ... }
                # }
                statics.id_list = cache_data.get("id_list", [])
                issues = cache_data.get("issues", {})

                # Clear and re-populate issues_hash
                statics.issues_hash.clear()
                for doc_id, doc_data in issues.items():
                    statics.issues_hash.__setitem__(doc_id, doc_data)

            print("Loaded issues from local cache.")
        except Exception as e:
            print(f"Error loading local cache: {e}")
            # If anything goes wrong, fallback to fetching from DB
            self.set_issues()
            self.save_local_cache()

    def save_local_cache(self):
        """
        Save `statics.id_list` and `statics.issues_hash` to local JSON file.
        """
        try:
            # Convert `statics.issues_hash` into a normal dict if it's a custom type
            # If `issues_hash` is a normal dict, you can do it directly:
            issues_dict = dict(statics.issues_hash)  # or use a loop if needed

            cache_data = {
                "id_list": statics.id_list,
                "issues": issues_dict
            }
            with open(self.local_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
            print("Local cache saved to disk.")
        except Exception as e:
            print(f"Error saving local cache: {e}")

    # --------------------------------------------------
    #   Microsoft Auth Stubs (if needed)
    # --------------------------------------------------
    def get_microsoft_auth_token(self):
        print("Getting Microsoft Auth Token... (stub)")

    def verify_microsoft_token(self, token):
        print("Verifying Microsoft token... (stub)")
