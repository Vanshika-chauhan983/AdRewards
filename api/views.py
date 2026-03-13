from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import auth_service, ad_service, wallet_service, settings_service
from django.http import JsonResponse
from datetime import datetime

# -------------------------
# Public Health Check
# -------------------------
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "API is working",
            "timestamp": str(datetime.now())
        })


# -------------------------
# Authentication / Login
# -------------------------
class LoginView(APIView):
    def post(self, request):
        try:
            user_token = request.user
            user = auth_service.login_with_token(user_token)

            return Response({
                "message": "Login successful",
                "user": user
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminLoginView(APIView):
    def post(self, request):
        try:
            user_token = request.user
            user_profile = auth_service.get_user_profile(user_token["uid"])

            if user_profile.get("role") != "admin":
                return Response(
                    {"error": "Access denied. Admin only."},
                    status=status.HTTP_403_FORBIDDEN
                )

            return Response({
                "success": True,
                "message": "Admin login successful",
                "admin": {
                    "uid": user_token["uid"],
                    "email": user_token.get("email")
                }
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


# -------------------------
# User Profile
# -------------------------
class ProfileView(APIView):
    def get(self, request):
        try:
            user = auth_service.get_user_profile(request.user["uid"])
            return Response(user)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# Admin User Management
# -------------------------
class UserListView(APIView):
    def get(self, request):
        try:
            users = auth_service.get_all_users()
            return Response(users)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ToggleUserStatusView(APIView):
    def post(self, request):
        try:
            uid = request.data.get("uid")
            is_blocked = request.data.get("isBlocked")

            result = auth_service.update_user_status(uid, is_blocked)
            return Response(result)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# Ads
# -------------------------
class CreateAdView(APIView):
    def post(self, request):
        try:
            ad_data = request.data

            if not ad_data.get("title") or not ad_data.get("mediaUrl") or not ad_data.get("mediaType"):
                return Response(
                    {"error": "Missing required fields"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_ad = ad_service.create_ad(ad_data)
            return Response(new_ad, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedView(APIView):
    def get(self, request):
        try:
            user_id = request.user["uid"]
            ads = ad_service.fetch_ads(user_id)
            return Response(ads)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompleteAdView(APIView):
    def post(self, request):
        try:
            ad_id = request.data.get("adId")
            user_id = request.user["uid"]

            result = ad_service.mark_ad_complete(user_id, ad_id)
            return Response(result)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# Wallet
# -------------------------
class BalanceView(APIView):
    def get(self, request):
        try:
            balance = wallet_service.get_balance(request.user["uid"])
            return Response({"balance": balance})

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RedeemPointsView(APIView):
    def post(self, request):
        try:
            amount = request.data.get("amount")
            payment_method = request.data.get("paymentMethod")
            payment_details = request.data.get("paymentDetails")

            result = wallet_service.redeem_points(
                request.user["uid"],
                amount,
                payment_method,
                payment_details
            )

            return Response(result)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# Settings (Admin Only)
# -------------------------
class SettingsView(APIView):
    def get(self, request):
        try:
            user = auth_service.get_user_profile(request.user["uid"])

            if user.get("role") != "admin":
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            settings = settings_service.get_settings()
            return Response(settings)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            user = auth_service.get_user_profile(request.user["uid"])

            if user.get("role") != "admin":
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            result = settings_service.update_settings(request.data)
            return Response(result)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
