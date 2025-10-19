from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    ProfileSerializer,
    ProfileRetrieveSerializer,
    VerificationCodeSerializer,
    SendVerificationCodeSerializer,
)
from .utils import send_verification_email, generate_verification_code
from datetime import timedelta
import random

from .models import User
from .permissions import IsVerified


class SignupView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Send verification code
            user.verification_code = generate_verification_code()
            user.code_updated_at = timezone.now()
            user.save()
            send_verification_email(user.email, user.verification_code)
            
            token = serializer.get_token(user)
            return Response(
                {
                    "message": "User created successfully",
                    "email": user.email,
                    "access": token['access'],
                    "refresh": token['refresh'],
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendVerificationCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_verified:
            return Response(
                {"message": "User already verified"}, status=status.HTTP_409_CONFLICT
            )
        if user.code_updated_at < now() - timedelta(minutes=15):
            user.verification_code = generate_verification_code()
            user.try_count = 0
            user.code_updated_at = now()
            user.save()

        if user.try_count >= 3:
            return Response(
                {"message": "Try again after 15 minutes"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        else:
            send_verification_email(user.email, user.verification_code)
            user.try_count += 1
            user.save()
            return Response(
                {"message": "Verification Code sent successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )


class VerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.code_updated_at < now() - timedelta(minutes=15):
            return Response(
                {"message": "Verification Code has expired"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        serializer = VerificationCodeSerializer(data=request.data)
        if serializer.is_valid():
            if (int(serializer.validated_data.get("verification_code")) == user.verification_code):
                user.is_verified = True
                user.status = 'verified'
                user.email_verified_at = now()
                user.save()
                return Response(
                    {"message": "User verified successfully"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "Verification Code is not correct"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = serializer.get_token(user)
            
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.save()
            
            return Response({
                "message": "Login successful",
                "access": token['access'],
                "refresh": token['refresh'],
                "user": ProfileRetrieveSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get(self, request):
        serializer = ProfileRetrieveSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileSerializer(instance=request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Refresh JWT access token using refresh token
        """
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate and create new access token from refresh token
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            
            return Response({
                'access': new_access_token
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Invalid or expired refresh token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

