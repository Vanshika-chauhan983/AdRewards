import firebase_admin
from firebase_admin import credentials
from django.conf import settings
import os
import json

def initialize():
    if not firebase_admin._apps:
        # Check if the environment variable for credentials exists (Cloud Deployment)
        firebase_cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

        if firebase_cred_json:
            try:
                cred_dict = json.loads(firebase_cred_json)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable is not valid JSON")
        else:
            # Fallback for local development
            cred_path = os.path.join(settings.BASE_DIR, 'ServiceAccountKey.json')
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"Firebase service account file not found. Either provide "
                    f"FIREBASE_SERVICE_ACCOUNT_KEY env var or place it at {cred_path}"
                )
            cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred)
