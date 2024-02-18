# firebase_manager.py
import os
import time

import firebase_admin
import requests
from firebase_admin import credentials, firestore, auth
from msal import PublicClientApplication

import statics


class FirebaseManager:
    # issues_hash = hash_table.HashTable(50)
    def __init__(self):
        script_dir = os.path.dirname(__file__)
        json_path = os.path.join(script_dir, "firebaseadminsdk.json")
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://job-card.firebaseio.com',
        }, name='issues_app')
        app = firebase_admin.get_app(name='issues_app')
        statics.firestoredb = firestore.client(app=app)

    def save_data(self, collection_name, data, document=None):
        try:
            # Save job card data to Firestore
            if document:
                doc_ref = statics.firestoredb.collection(collection_name).document(document).set(data, True)
            else:
                doc_ref = statics.firestoredb.collection(collection_name).add(data)

            print(f"Data to save to Firestore {data}")
            print(f"Data saved to Firestore with ID: {doc_ref}")
        except Exception as e:
            print(f"Error saving data to Firestore: {e}")

    def get_data(self, collection_name, document_name):
        try:
            doc_ref = statics.firestoredb.collection(collection_name).document(document_name)
            doc = doc_ref.get().to_dict().values()
            print(f"Firebase Data = {doc}")
            return doc
        except Exception as e:
            print(f"Error fetching collection from Firestore: {e}")
            return []

    def set_issues(self):
        try:
            # Fetch job card data from Firestore
            issues_coll = statics.firestoredb.collection(u'issues').get()

            for int in range(len(issues_coll)):
                statics.issues_hash.__setitem__(issues_coll[int].id, issues_coll[int].to_dict())
                statics.id_list.insert(int, issues_coll[int].id)

            # for doc_snapshot in issues_coll:
            # self.issuesDict.append(doc_snapshot.to_dict())
            # print("id == " + doc_snapshot.id)
            # print("get( == " + doc_snapshot.get('end_date'))
            # print("to_dict == " + str(doc_snapshot.to_dict()))

            print(statics.issues_hash)



        except Exception as e:
            print(f"Error fetching issues from Firestore: {e}")

    def get_microsoft_auth_token(self):
        print("Getting Microsoft Auth Token")

    def verify_microsoft_token(self, token):
        print("Verifying Microsoft")
