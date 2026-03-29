from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth as firebase_auth
from .models import UserProfile

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

        uid = decoded_token["uid"]

        # ✅ Auto create user if not exists
        user, created = UserProfile.objects.get_or_create(
            uid=uid,
            defaults={
                "email": decoded_token.get("email"),
                "phone_number": decoded_token.get("phone_number")
            }
        )

        return (user, None)