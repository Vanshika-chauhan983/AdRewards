
from django.urls import path
from . import views

urlpatterns = [
    path('status', views.health_check),
    
    # Auth
    path('auth/login', views.LoginView.as_view()),
    path('auth/profile', views.ProfileView.as_view()),
    path('auth/users', views.UserListView.as_view()),
    path('auth/users/toggle-status', views.ToggleUserStatusView.as_view()), # Updated
    
    # Admin
    path('admin/login', views.AdminLoginView.as_view()),
    
    # Ads
    path('ads/feed', views.FeedView.as_view()), # Updated: /api/ads/feed
    path('ads', views.CreateAdView.as_view()),  # Updated: POST /api/ads
    path('ads/complete', views.CompleteAdView.as_view()),
    path('ads/stats', views.StatsView.as_view()),
    
    # Wallet
    path('wallet/balance', views.BalanceView.as_view()),
    path('wallet/redeem', views.RedeemPointsView.as_view()), # Added redeem
    
    # Settings
    path('settings', views.SettingsView.as_view()),
    path('settings/', views.SettingsView.as_view()),
]
