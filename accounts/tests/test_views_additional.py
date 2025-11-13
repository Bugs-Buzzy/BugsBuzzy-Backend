from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(email="verified@example.com")
    user.is_verified = True
    user.status = "verified"
    user.phone_number = "09123456789"
    user.national_code = "1234567891"
    user.save()
    return user


@pytest.mark.django_db
def test_check_email_requires_email(api_client):
    url = reverse("check_email")
    response = api_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Email is required"


@pytest.mark.django_db
def test_check_email_validates_format(api_client):
    url = reverse("check_email")
    response = api_client.post(url, {"email": "invalid"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Invalid email format"


@pytest.mark.django_db
def test_check_email_returns_existing_user_info(api_client):
    user = User.objects.create_user(email="exists@example.com", password="pass1234")
    url = reverse("check_email")
    response = api_client.post(url, {"email": "exists@example.com"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["exists"] is True
    assert response.data["has_usable_password"] is True


@pytest.mark.django_db
def test_send_code_rejects_invalid_email_format(api_client):
    url = reverse("send_code")
    response = api_client.post(url, {"email": "bad"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Invalid email format"


@pytest.mark.django_db
def test_send_code_rate_limits_after_three_attempts(api_client):
    user = User.objects.create_user(email="repeat@example.com")
    user.verification_code = 123456
    user.code_updated_at = timezone.now()
    user.try_count = 3
    user.save()

    url = reverse("send_code")
    response = api_client.post(url, {"email": "repeat@example.com"}, format="json")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_verify_code_requires_fields(api_client):
    url = reverse("verify_code")
    response = api_client.post(url, {"email": "user@example.com"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_verify_code_rejects_expired_code(api_client):
    user = User.objects.create_user(email="expired@example.com")
    user.verification_code = 123456
    user.code_updated_at = timezone.now() - timedelta(minutes=16)
    user.save()

    url = reverse("verify_code")
    response = api_client.post(
        url,
        {"email": "expired@example.com", "verification_code": "123456"},
        format="json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.data["message"] == "Verification code has expired"


@pytest.mark.django_db
def test_verify_code_rejects_wrong_code(api_client):
    user = User.objects.create_user(email="wrong@example.com")
    user.verification_code = 123456
    user.code_updated_at = timezone.now()
    user.save()

    url = reverse("verify_code")
    response = api_client.post(
        url,
        {"email": "wrong@example.com", "verification_code": "654321"},
        format="json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.data["message"] == "Invalid verification code"


@pytest.mark.django_db
def test_login_requires_email_and_password(api_client):
    url = reverse("login")
    response = api_client.post(url, {"email": ""}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(api_client):
    User.objects.create_user(email="login@example.com", password="pass1234")
    url = reverse("login")
    response = api_client.post(
        url,
        {"email": "login@example.com", "password": "wrong"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_rejects_inactive_user(api_client):
    user = User.objects.create_user(email="inactive@example.com", password="pass1234")
    user.is_active = False
    user.save()

    url = reverse("login")
    response = api_client.post(
        url,
        {"email": "inactive@example.com", "password": "pass1234"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_profile_get_returns_data(api_client, verified_user):
    token = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    url = reverse("profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == "verified@example.com"


@pytest.mark.django_db
def test_forgot_password_requires_valid_code(api_client):
    user = User.objects.create_user(email="forgot@example.com")
    user.verification_code = 123456
    user.code_updated_at = timezone.now()
    user.save()

    url = reverse("forgot_password")
    response = api_client.post(
        url,
        {"email": "forgot@example.com", "verification_code": "654321"},
        format="json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.data["message"] == "Invalid verification code"


@pytest.mark.django_db
def test_forgot_password_rejects_expired_code(api_client):
    user = User.objects.create_user(email="late@example.com")
    user.verification_code = 123456
    user.code_updated_at = timezone.now() - timedelta(minutes=16)
    user.save()

    url = reverse("forgot_password")
    response = api_client.post(
        url,
        {"email": "late@example.com", "verification_code": "123456"},
        format="json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.data["message"] == "Verification code has expired"


@pytest.mark.django_db
def test_change_password_requires_new_password(api_client, verified_user):
    token = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    url = reverse("change_password")
    response = api_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "New password is required"


@pytest.mark.django_db
def test_change_password_requires_current_when_usable(api_client, verified_user):
    verified_user.set_password("oldpass123")
    verified_user.save()

    token = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    url = reverse("change_password")
    response = api_client.post(url, {"new_password": "Newpass123"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Current password is required"


@pytest.mark.django_db
def test_change_password_rejects_wrong_current(api_client, verified_user):
    verified_user.set_password("oldpass123")
    verified_user.save()

    token = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    url = reverse("change_password")
    response = api_client.post(
        url,
        {"current_password": "wrong", "new_password": "Newpass123"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Current password is incorrect"


@pytest.mark.django_db
def test_token_refresh_returns_new_token(api_client, verified_user):
    refresh = RefreshToken.for_user(verified_user)
    url = reverse("token_refresh")
    response = api_client.post(url, {"refresh": str(refresh)}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_token_refresh_rejects_invalid_token(api_client):
    url = reverse("token_refresh")
    response = api_client.post(url, {"refresh": "invalid"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid or expired refresh token"
