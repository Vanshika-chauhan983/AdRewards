
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
         # Initialize Firebase when app is ready
         from . import firebase_setup
         firebase_setup.initialize()
