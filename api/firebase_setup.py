
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings
import os

_db = None

def initialize():
    global _db
    if not firebase_admin._apps:
        # Path to service account key
        cred_path = os.path.join(settings.BASE_DIR, 'ServiceAccountKey.json')
        
        if not os.path.exists(cred_path):
            print(f"WARNING: ServiceAccountKey.json not found at {cred_path}")
            return

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        print("Firebase Admin Initialized")
    else:
        _db = firestore.client()

def get_db():
    global _db
    if _db is None:
        initialize()
    return _db
