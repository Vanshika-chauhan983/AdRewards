
from ..firebase_setup import get_db

def get_settings():
    db = get_db()
    settings_doc = db.collection('settings').document('global').get()

    if not settings_doc.exists:
        # Default settings matching Node.js backend
        return {
            'maintenanceMode': False,
            'notificationsEnabled': True,
            'contactEmail': 'admin@advertising-app.com',
            'twoFactorEnabled': True
        }

    return settings_doc.to_dict()

def update_settings(settings_data):
    db = get_db()
    db.collection('settings').document('global').set(settings_data, merge=True)
    return {'success': True, 'settings': settings_data}
