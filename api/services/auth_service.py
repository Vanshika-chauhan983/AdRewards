
from ..firebase_setup import get_db
from datetime import datetime

def login_with_token(decoded_token):
    db = get_db()
    uid = decoded_token.get('uid')
    phone_number = decoded_token.get('phone_number')
    email = decoded_token.get('email')

    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        new_user = {
            'uid': uid,
            'phone_number': phone_number,
            'email': email,
            'createdAt': datetime.now().isoformat(),
            'walletBalance': 0,
            'role': 'user',
            'isBlocked': False
        }
        user_ref.set(new_user)
        return new_user

    user_data = user_doc.to_dict()
    if user_data.get('isBlocked'):
        raise Exception("User account is blocked")

    return user_data

def get_user_profile(uid):
    db = get_db()
    user_doc = db.collection('users').document(uid).get()
    
    if not user_doc.exists:
        raise Exception("User not found")
        
    return user_doc.to_dict()

def get_all_users():
    db = get_db()
    docs = db.collection('users').stream()
    users = []
    for doc in docs:
        d = doc.to_dict()
        d['uid'] = doc.id
        users.append(d)
    return users

def update_user_status(uid, is_blocked):
    db = get_db()
    db.collection('users').document(uid).update({
        'isBlocked': is_blocked
    })
    return {'success': True}

def make_admin(uid):
    db = get_db()
    db.collection('users').document(uid).update({
        'role': 'admin'
    })
    return {'success': True, 'message': "User promoted to admin"}
