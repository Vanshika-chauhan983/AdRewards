
from django.urls import path
from . import views

urlpatterns = [
    path('status', views.HealthCheckView.as_view()),
    
    # Auth
    path('auth/login', views.LoginView.as_view()),
    path('auth/profile', views.ProfileView.as_view()),
   
    # Ads
    path('ads/feed', views.FeedView.as_view()),   
    path('ads/complete', views.CompleteAdView.as_view()),
    
    # Wallet
    path('wallet/balance', views.BalanceView.as_view()),
    path('wallet/redeem', views.RedeemPointsView.as_view()), 
]
