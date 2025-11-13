import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from accounts.serializers import (
    ProfileSerializer,
    SendVerificationCodeSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


@pytest.mark.django_db
def test_registration_serializer_password_mismatch():
    serializer = UserRegistrationSerializer(
        data={
            "email": "user@example.com",
            "password": "Str0ngPass!1",
            "password_confirm": "Diff3rentPass!2",
        }
    )

    assert serializer.is_valid() is False
    assert "Passwords don't match." in str(serializer.errors)


@pytest.mark.django_db
def test_registration_serializer_validate_email_custom_message():
    User.objects.create_user(email="user@example.com")

    serializer = UserRegistrationSerializer()

    with pytest.raises(ValidationError) as exc:
        serializer.validate_email("user@example.com")

    assert "User already exists." in str(exc.value)


@pytest.mark.django_db
def test_registration_serializer_create_sets_password():
    serializer = UserRegistrationSerializer(
        data={
            "email": "new@example.com",
            "password": "Str0ngPass!1",
            "password_confirm": "Str0ngPass!1",
        }
    )
    assert serializer.is_valid() is True

    user = serializer.save()
    assert user.check_password("Str0ngPass!1") is True


@pytest.mark.django_db
def test_login_serializer_requires_credentials():
    serializer = UserLoginSerializer()

    with pytest.raises(ValidationError) as exc:
        serializer.validate({})

    assert "Must include email and password." in str(exc.value)


@pytest.mark.django_db
def test_login_serializer_rejects_disabled_user(monkeypatch):
    user = User.objects.create_user(email="disabled@example.com", password="Str0ngPass!1")
    user.is_active = False
    user.save()

    def fake_authenticate(username=None, password=None):
        assert username == "disabled@example.com"
        assert password == "Str0ngPass!1"
        return user

    monkeypatch.setattr("accounts.serializers.authenticate", fake_authenticate)

    serializer = UserLoginSerializer(
        data={"email": "disabled@example.com", "password": "Str0ngPass!1"}
    )

    with pytest.raises(ValidationError) as exc:
        serializer.is_valid(raise_exception=True)

    assert "User account is disabled." in str(exc.value)


@pytest.mark.django_db
def test_send_verification_code_serializer_validates_status():
    user = User.objects.create_user(email="verify@example.com")
    user.is_verified = True
    user.save()

    serializer = SendVerificationCodeSerializer(data={"email": "verify@example.com"})

    assert serializer.is_valid() is False
    assert "User is already verified." in str(serializer.errors)


@pytest.mark.django_db
def test_send_verification_code_serializer_missing_user():
    serializer = SendVerificationCodeSerializer(data={"email": "missing@example.com"})

    assert serializer.is_valid() is False
    assert "User with this email does not exist." in str(serializer.errors)


@pytest.mark.django_db
def test_profile_serializer_duplicate_phone_number():
    existing = User.objects.create_user(email="first@example.com")
    existing.phone_number = "09123456780"
    existing.national_code = "1234567891"
    existing.save()

    user = User.objects.create_user(email="second@example.com")
    user.phone_number = "09123456781"
    user.national_code = "1234567892"
    user.save()

    serializer = ProfileSerializer(
        instance=user,
        data={
            "first_name": "علی",
            "last_name": "احمدی",
            "phone_number": "09123456780",
            "gender": "M",
            "national_code": "1234567892",
            "city": "تهران",
            "university": "",
            "major": "",
        },
    )

    assert serializer.is_valid() is False
    assert "phone number" in str(serializer.errors).lower()


@pytest.mark.django_db
def test_profile_serializer_national_code_validation():
    user = User.objects.create_user(email="third@example.com")
    user.phone_number = "09123456789"
    user.national_code = "1234567891"
    user.save()

    serializer = ProfileSerializer(
        instance=user,
        data={
            "first_name": "علی",
            "last_name": "احمدی",
            "phone_number": "09123456789",
            "gender": "M",
            "national_code": "abc",
            "city": "تهران",
            "university": "",
            "major": "",
        },
    )

    assert serializer.is_valid() is False
    assert "national code" in str(serializer.errors).lower()


@pytest.mark.django_db
def test_profile_serializer_requires_persian_names():
    user = User.objects.create_user(email="fourth@example.com")
    user.phone_number = "09123456789"
    user.national_code = "1234567891"
    user.save()

    serializer = ProfileSerializer(
        instance=user,
        data={
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "09123456789",
            "gender": "M",
            "national_code": "1234567891",
            "city": "تهران",
            "university": "",
            "major": "",
        },
    )

    assert serializer.is_valid() is False
    assert "first name should be in persian" in str(serializer.errors).lower()
