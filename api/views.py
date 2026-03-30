from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from datetime import datetime
from .models import Ad, AdView, Transaction, RedemptionRequest

# -------------------------
# Public Health Check
# -------------------------
class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return JsonResponse({"status": "ok"})


# -------------------------
# Authentication / Login
# -------------------------
class LoginView(APIView):
    def post(self, request):
        try:
            user = request.user

            return Response({
                "message": "Login successful",
                "user": {
                    "uid": user.uid,
                    "email": user.email,
                    "wallet_balance": user.wallet_balance,
                    "role": user.role
                }
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# User Profile
# -------------------------
class ProfileView(APIView):
    def get(self, request):
        user = request.user

        return Response({
            "uid": user.uid,
            "email": user.email,
            "phone": user.phone_number,
            "wallet_balance": user.wallet_balance,
            "role": user.role
        })

# -------------------------
# Ads
# -------------------------

class FeedView(APIView):
    def get(self, request):
        ads = Ad.objects.filter(active=True).values()
        return Response(list(ads))


class CompleteAdView(APIView):
    def post(self, request):
        user = request.user
        ad_id = request.data.get("adId")

        try:
            ad = Ad.objects.get(id=ad_id)
        except Ad.DoesNotExist:
            return Response({"error": "Ad not found"}, status=404)

        # Prevent duplicate reward
        if AdView.objects.filter(user=user, ad=ad).exists():
            return Response({"message": "Already claimed"})

        # Create AdView
        AdView.objects.create(
            user=user,
            ad=ad,
            reward=ad.point_reward
        )

        # Update wallet
        user.wallet_balance += ad.point_reward
        user.save()

        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=ad.point_reward,
            type="credit",
            description="Ad reward"
        )

        # Increment ad views
        ad.view_count += 1
        ad.save()

        return Response({"message": "Reward credited"})


# -------------------------
# Wallet
# -------------------------
class BalanceView(APIView):
    def get(self, request):
        return Response({
            "balance": request.user.wallet_balance
        })


class RedeemPointsView(APIView):
    def post(self, request):
        user = request.user

        amount = float(request.data.get("amount", 0))
        payment_method = request.data.get("paymentMethod")
        payment_details = request.data.get("paymentDetails")

        if user.wallet_balance < amount:
            return Response({"error": "Insufficient balance"}, status=400)

        # Deduct balance
        user.wallet_balance -= amount
        user.save()

        # Create redemption request
        RedemptionRequest.objects.create(
            user=user,
            amount=amount,
            payment_method=payment_method,
            payment_details=payment_details
        )

        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=amount,
            type="debit",
            description="Redeem request"
        )

        return Response({"message": "Request submitted"})
