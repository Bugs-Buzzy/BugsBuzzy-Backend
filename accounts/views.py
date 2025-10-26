from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    ProfileSerializer,
    ProfileRetrieveSerializer,
    VerificationCodeSerializer,
)
from .utils import send_verification_email, generate_verification_code, normalize_email
from .throttling import CheckEmailThrottle
from datetime import timedelta
import re

from .models import User
from .permissions import IsVerified

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class CheckEmailView(APIView):
    """
    Check if email exists and if user has usable password
    No authentication required, rate limited to 3 requests per minute
    """

    permission_classes = [AllowAny]
    throttle_classes = [CheckEmailThrottle]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        if not EMAIL_REGEX.match(email):
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email_value = normalize_email(email)

        try:
            user = User.objects.get(email=normalized_email_value)
            return Response(
                {
                    "exists": True,
                    "has_usable_password": user.has_usable_password(),
                },
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "exists": False,
                    "has_usable_password": False,
                },
                status=status.HTTP_200_OK,
            )


class SendCodeView(APIView):
    """
    Send verification code to email (works for both new and existing users)
    No authentication required
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        if not EMAIL_REGEX.match(email):
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email_value = normalize_email(email)

        # Get or create user
        user, created = User.objects.get_or_create(
            email=normalized_email_value,
            defaults={
                "normalized_email": normalized_email_value,
            },
        )

        # If new user, set unusable password
        if created:
            user.set_unusable_password()
            user.save()

        # Check rate limiting and code validity
        if (
            not created
            and user.verification_code
            and user.code_updated_at
            and user.code_updated_at > now() - timedelta(minutes=15)
        ):
            # Code is still valid
            if user.try_count >= 3:
                return Response(
                    {"message": "Too many attempts. Please try again after 15 minutes"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            # Increment try count and send existing code
            user.try_count += 1
            user.save()
            send_verification_email(user.email, user.verification_code)
        else:
            # Generate new code and send
            user.verification_code = generate_verification_code()
            user.code_updated_at = now()
            user.try_count = 1
            user.save()
            send_verification_email(user.email, user.verification_code)

        return Response(
            {
                "message": "Verification code sent to your email",
                "is_new_user": created or not user.has_usable_password(),
            },
            status=status.HTTP_200_OK,
        )


class VerifyCodeView(APIView):
    """
    Verify code and login/complete registration
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("verification_code")
        password = request.data.get("password")  # Only for new users

        if not email or not code:
            return Response(
                {"message": "Email and verification code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        if not EMAIL_REGEX.match(email):
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email_value = normalize_email(email)

        try:
            user = User.objects.get(email=normalized_email_value)
        except User.DoesNotExist:
            return Response({"message": "Invalid email"}, status=status.HTTP_404_NOT_FOUND)

        # Check code expiration
        if user.code_updated_at < now() - timedelta(minutes=15):
            return Response(
                {"message": "Verification code has expired"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Verify code
        if int(code) != user.verification_code:
            return Response(
                {"message": "Invalid verification code"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Mark as verified and invalidate the code
        user.is_verified = True
        user.status = "verified"
        user.email_verified_at = now()
        user.verification_code = None
        user.code_updated_at = None
        user.try_count = 0
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Verification successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": ProfileRetrieveSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    Login with email and password
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"message": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate email format
        if not EMAIL_REGEX.match(email):
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email_value = normalize_email(email)

        try:
            user = User.objects.get(email=normalized_email_value)
        except User.DoesNotExist:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"message": "Account is disabled"}, status=status.HTTP_401_UNAUTHORIZED)

        # Update last login
        user.last_login_ip = request.META.get("REMOTE_ADDR")
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": ProfileRetrieveSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request):
        serializer = ProfileRetrieveSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileSerializer(instance=request.user, data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.save()
            user.profile_completed = True
            user.save()
            return Response({"message": "Profile updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """
    Reset password by verifying email code
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("verification_code")

        if not email or not code:
            return Response(
                {"message": "Email and verification code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        if not EMAIL_REGEX.match(email):
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email_value = normalize_email(email)

        try:
            user = User.objects.get(email=normalized_email_value)
        except User.DoesNotExist:
            return Response({"message": "Invalid email"}, status=status.HTTP_404_NOT_FOUND)

        # Check code expiration
        if user.code_updated_at < now() - timedelta(minutes=15):
            return Response(
                {"message": "Verification code has expired"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Verify code
        if int(code) != user.verification_code:
            return Response(
                {"message": "Invalid verification code"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Mark as verified, make password unusable, and invalidate the code
        user.is_verified = True
        user.status = "verified"
        user.email_verified_at = now()
        user.set_unusable_password()
        user.verification_code = None
        user.code_updated_at = None
        user.try_count = 0
        user.save()

        # Generate tokens for login
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Password reset successful. Please set a new password in your profile.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": ProfileRetrieveSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not new_password:
            return Response(
                {"message": "New password is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # If user has a usable password, verify current password
        if user.has_usable_password():
            if not current_password:
                return Response(
                    {"message": "Current password is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            if not user.check_password(current_password):
                return Response(
                    {"message": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST
                )

        # Validate new password
        if len(new_password) < 8:
            return Response(
                {"message": "Password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            return Response({"access": new_access_token}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
