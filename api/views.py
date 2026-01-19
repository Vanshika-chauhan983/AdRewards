
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import auth_service, ad_service, wallet_service, settings_service
from django.http import JsonResponse
import json
from firebase_admin import auth as firebase_auth
from datetime import datetime

def get_user_from_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

class LoginView(APIView):
    def post(self, request):
        user_token = get_user_from_token(request)
        if not user_token:
             # If validation fails in get_user_from_token, we can try to see if body has it? 
             # Node: verifies token in header.
             return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            user = auth_service.login_with_token(user_token)
            return Response({
                'message': 'Login successful',
                'user': user
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminLoginView(APIView):
    def post(self, request):
        user_token = get_user_from_token(request)
        if not user_token:
            return Response({'error': "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            # Check if user exists and is admin
            user_profile = auth_service.get_user_profile(user_token['uid'])
            
            if user_profile.get('role') != 'admin':
                return Response({'error': "Access denied. Admin only."}, status=status.HTTP_403_FORBIDDEN)
                
            return Response({
                'success': True,
                'message': "Admin login successful",
                'admin': {
                    'uid': user_token['uid'],
                    'email': user_token.get('email')
                }
            })
            
        except Exception as e:
             # Node returns 403 on error in try/catch (invalid or expired or not found)
             return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

class ProfileView(APIView):
    def get(self, request):
        user_token = get_user_from_token(request)
        if not user_token:
             return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
             
        try:
            user = auth_service.get_user_profile(user_token['uid'])
            return Response(user)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserListView(APIView):
    def get(self, request):
        try:
            users = auth_service.get_all_users()
            return Response(users)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ToggleUserStatusView(APIView):
    def post(self, request):
        try:
            uid = request.data.get('uid')
            # Handle boolean explicitly as it might come as string or bool
            is_blocked = request.data.get('isBlocked')
            result = auth_service.update_user_status(uid, is_blocked)
            return Response(result)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateAdView(APIView):
    def post(self, request):
        user_token = get_user_from_token(request)
        
        try:
            ad_data = request.data
            
            if not ad_data.get('title') or not ad_data.get('mediaUrl') or not ad_data.get('mediaType'):
                return Response({'error': "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
                
            new_ad = ad_service.create_ad(ad_data)
            return Response(new_ad, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FeedView(APIView):
    def get(self, request):
        try:
            user_token = get_user_from_token(request)
            user_id = user_token['uid'] if user_token else None
            ads = ad_service.fetch_ads(user_id)
            return Response(ads)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompleteAdView(APIView):
    def post(self, request):
        try:
            user_token = get_user_from_token(request)
            if not user_token:
                return Response({'error': "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
                
            ad_id = request.data.get('adId')
            user_id = user_token['uid']
            
            result = ad_service.mark_ad_complete(user_id, ad_id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StatsView(APIView):
    def get(self, request):
        try:
            stats = ad_service.get_dashboard_stats()
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BalanceView(APIView):
    def get(self, request):
        user_token = get_user_from_token(request)
        if not user_token:
             return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            balance = wallet_service.get_balance(user_token['uid'])
            # Match Node: res.status(200).json({ balance });
            return Response({'balance': balance})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RedeemPointsView(APIView):
    def post(self, request):
        user_token = get_user_from_token(request)
        if not user_token:
             return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            amount = request.data.get('amount')
            payment_method = request.data.get('paymentMethod')
            payment_details = request.data.get('paymentDetails')
            
            result = wallet_service.redeem_points(user_token['uid'], amount, payment_method, payment_details)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SettingsView(APIView):
    def get(self, request):
        # Verify admin
        user_token = get_user_from_token(request)
        if not user_token:
            return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # We should check admin role here properly using get_user_profile but for speed trusting token check from middleware in JS... 
        # But JS uses `verifyAdmin` middleware which checks DB.
        # I'll enable role check via service call to be safe.
        try:
            user = auth_service.get_user_profile(user_token['uid'])
            if user.get('role') != 'admin':
                  return Response({'error': "Access denied"}, status=status.HTTP_403_FORBIDDEN)
            
            settings = settings_service.get_settings()
            return Response(settings)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        # Verify admin
        user_token = get_user_from_token(request)
        if not user_token:
            return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            user = auth_service.get_user_profile(user_token['uid'])
            if user.get('role') != 'admin':
                  return Response({'error': "Access denied"}, status=status.HTTP_403_FORBIDDEN)

            result = settings_service.update_settings(request.data)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def health_check(request):
    return JsonResponse({'status': 'API is working', 'timestamp': str(datetime.now())})
