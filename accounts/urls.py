from django.urls import path
from . import views

urlpatterns = [
    path("check-email/", views.CheckEmailView.as_view(), name="check_email"),
    path("send-code/", views.SendCodeView.as_view(), name="send_code"),
    path("verify-code/", views.VerifyCodeView.as_view(), name="verify_code"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token_refresh"),
]
