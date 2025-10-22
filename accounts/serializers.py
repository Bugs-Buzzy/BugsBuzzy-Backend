import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .utils import send_verification_email, normalize_email


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm"]
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # Create user
        user = User.objects.create_user(email=validated_data["email"])
        user.set_password(password)

        return user

    def get_token(self, user):
        """Generate JWT token for the user"""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(username=normalize_email(email), password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("Must include email and password.")

        return attrs

    def get_token(self, user):
        """Generate JWT token for the user"""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "national_code",
            "phone_number",
            "gender",
            "birth_date",
            "city",
            "university",
            "major",
            "is_verified",
            "status",
            "created_at",
            "last_login",
            "last_login_ip",
            "email_verified_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "national_code",
            "is_verified",
            "status",
            "created_at",
            "last_login",
            "last_login_ip",
            "email_verified_at",
        ]


# class UserUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = [
#             'first_name', 'last_name', 'phone_number', 'gender',
#             'birth_date', 'city', 'university', 'major'
#         ]

#     def validate_phone_number(self, value):
#         # Check if phone number is already taken by another user
#         if User.objects.filter(phone_number=value).exclude(id=self.instance.id).exists():
#             raise serializers.ValidationError("A user with this phone number already exists.")
#         return value


class VerificationCodeSerializer(serializers.Serializer):
    verification_code = serializers.CharField(max_length=6, min_length=6)

    def validate_verification_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Verification code must contain only digits.")
        return value


class SendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        normalized_email = normalize_email(value)
        try:
            user = User.objects.get(email=normalized_email)
            if user.is_verified:
                raise serializers.ValidationError("User is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return normalized_email


class ProfileRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user profile data"""
    
    has_usable_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "national_code",
            "phone_number",
            "gender",
            "birth_date",
            "city",
            "university",
            "major",
            "is_verified",
            "status",
            "has_paid",
            "profile_completed",
            "has_usable_password",
            "created_at",
            "last_login",
            "last_login_ip",
            "email_verified_at",
        ]
        read_only_fields = [
            "email",
            "national_code",
            "is_verified",
            "status",
            "has_paid",
            "profile_completed",
            "has_usable_password",
            "created_at",
            "last_login",
            "last_login_ip",
            "email_verified_at",
        ]
    
    def get_has_usable_password(self, obj):
        return obj.has_usable_password()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "gender",
            "national_code",
            "city",
            "university",
            "major",
        ]
        extra_kwargs = {
            "university": {"required": False, "allow_blank": True},
            "major": {"required": False, "allow_blank": True},
        }

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate_national_code(self, value):
        if User.objects.filter(national_code=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this national code already exists.")

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("National code should contain only 10 digits.")

        national_code = int(value)
        control = national_code % 10
        national_code //= 10

        sum_ = 0
        for i in range(2, 11):
            digit = national_code % 10
            sum_ += digit * i
            national_code //= 10

        remainder = sum_ % 11
        new_control = remainder if remainder < 2 else 11 - remainder

        if new_control != control:
            raise serializers.ValidationError("National code is invalid.")

        return value

    def validate_first_name(self, value):
        if bool(re.match(r"^[\u0621-\u0651\u066B-\u06CC\u200c\s]+$", value)):
            return value
        raise serializers.ValidationError("First name should be in persian.")

    def validate_last_name(self, value):
        if bool(re.match(r"^[\u0621-\u0651\u066B-\u06CC\u200c\s]+$", value)):
            return value
        raise serializers.ValidationError("Last name should be in persian.")
