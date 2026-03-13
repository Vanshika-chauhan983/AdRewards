from ..firebase_setup import get_db


DEFAULT_SETTINGS = {
    'maintenanceMode': False,
    'notificationsEnabled': True,
    'contactEmail': 'admin@advertising-app.com',
    'twoFactorEnabled': True
}


ALLOWED_FIELDS = {
    'maintenanceMode',
    'notificationsEnabled',
    'contactEmail',
    'twoFactorEnabled'
}


def get_settings():
    db = get_db()
    settings_doc = db.collection('settings').document('global').get()

    if not settings_doc.exists:
        return DEFAULT_SETTINGS

    data = settings_doc.to_dict()

    # Ensure missing fields fallback to default
    for key, value in DEFAULT_SETTINGS.items():
        data.setdefault(key, value)

    return data


def update_settings(settings_data):
    db = get_db()

    # Filter only allowed fields
    filtered_data = {
        key: settings_data[key]
        for key in settings_data
        if key in ALLOWED_FIELDS
    }

    if not filtered_data:
        raise Exception("No valid settings provided")

    db.collection('settings').document('global').set(
        filtered_data,
        merge=True
    )

    return {
        'success': True,
        'settings': filtered_data
    }
