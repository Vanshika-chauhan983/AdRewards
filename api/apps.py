from django.apps import AppConfig
import sys

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Skip Firebase initialization during management commands
        management_commands = {
            'migrate',
            'makemigrations',
            'collectstatic',
            'shell',
            'test',
            'check'
        }

        # If any management command is running → skip
        if any(cmd in sys.argv for cmd in management_commands):
            return

        # Initialize Firebase safely
        try:
            from . import firebase_setup
            firebase_setup.initialize()
        except Exception as e:
            print(f"[Firebase Init Error]: {e}")