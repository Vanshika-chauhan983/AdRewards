
import os
import sys
import django
from django.conf import settings

def verify():
    print("Checking environment...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        django.setup()
        print("Django setup successful.")
    except Exception as e:
        print(f"Django setup failed: {e}")
        return

    print("Checking URL configuration...")
    try:
        from django.urls import reverse, resolve
        # Check a few URLs
        resolve('/api/status')
        resolve('/api/auth/login')
        resolve('/api/ads')
        print("URL resolution successful.")
    except Exception as e:
        print(f"URL resolution failed: {e}")
        return

    print("Checking Firebase configuration...")
    try:
        if os.path.exists('ServiceAccountKey.json'):
            print("ServiceAccountKey.json found.")
        else:
            print("WARNING: ServiceAccountKey.json NOT found.")
            
        # We can't easily check firebase init without actually initing, which happens in AppConfig
        from django.apps import apps
        api_config = apps.get_app_config('api')
        print(f"API App loaded: {api_config.name}")
    except Exception as e:
        print(f"Firebase/App check failed: {e}")
        return

    print("Verification passed!")

if __name__ == "__main__":
    verify()
