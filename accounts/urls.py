from django.urls import path
from . import views

urlpatterns = [
    # Class-based views
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # JWT token management
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification endpoints
    path('send-verification-code/', views.SendVerificationCodeView.as_view(), name='send_verification_code'),
    path('verify-email/', views.VerifyView.as_view(), name='verify_email'),
]
