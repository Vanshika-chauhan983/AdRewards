from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth as firebase_auth

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed("Authorization header missing")

        token = auth_header.split('Bearer ')[1]

        try:
            decoded_token = firebase_auth.verify_id_token(token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")

        return (decoded_token, None)
