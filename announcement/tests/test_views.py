import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from announcement.models import Announcement, UserAnnouncement


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="viewer@example.com",
        password="pass1234",
        national_code="3334567890",
        phone_number="09133333333",
        gender="M",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(title="Reminder", description="Don't forget")


@pytest.mark.django_db
@override_settings(
    APPEND_SLASH=False,
    DEBUG=True,
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=None,
)
def test_my_announcements_requires_authentication(api_client):
    url = reverse("my_announcements")
    response = api_client.get(url)

    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }


@pytest.mark.django_db
@override_settings(
    APPEND_SLASH=False,
    DEBUG=True,
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=None,
)
def test_my_announcements_returns_serialized_data(api_client, user, announcement):
    api_client.force_authenticate(user=user)

    ua1 = UserAnnouncement.objects.create(user=user, announcement=announcement)
    newer_announcement = Announcement.objects.create(title="Reminder 2", description="Notes")
    ua2 = UserAnnouncement.objects.create(user=user, announcement=newer_announcement)

    url = reverse("my_announcements")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]["announcement"]["title"] == "Reminder 2"
    assert response.data[0]["id"] == ua2.id
    assert response.data[1]["announcement"]["title"] == "Reminder"
